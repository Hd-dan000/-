import json
import os
import re
import time
from datetime import datetime

from database import get_db, dict_from_row, now_str
from config import UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS
from schemas import validate_training_create, validate_training_update, parse_json_field, serialize_json_field, TRAINING_STATUSES
from services.system_config_service import get_system_config_int
from services.maintenance_service import record_operation_log
from database_mysql import get_db as get_mysql_db
from routers import auth


def _get_teacher_info(teacher_id):
    """从 MySQL 查询教师基本信息"""
    db = get_mysql_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, college_id, school_id FROM teachers "
            "WHERE id = %s AND is_active = 1",
            (int(teacher_id),)
        )
        return cursor.fetchone()


def _get_fallback_school_id():
    """获取可用的学校 ID 兜底值"""
    db = get_mysql_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM schools WHERE is_active = 1 ORDER BY id LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row['id']
    return 1


def _generate_course_code(title, teacher_id):
    """生成唯一课程编号，长度控制在 30 字符以内"""
    base = re.sub(r'[^\w]', '', title or 'PROJECT')[:10].upper()
    suffix = f"{int(teacher_id)}{int(time.time() * 1000)}"[-18:]
    return f"{base}_{suffix}"[:30]


def _current_semester():
    """根据当前日期推断中国高校常见学期，如 2025-2026-1"""
    now = datetime.now()
    year, month = now.year, now.month
    if month >= 9:
        return f"{year}-{year + 1}-1"
    elif month >= 2:
        return f"{year - 1}-{year}-2"
    else:
        return f"{year - 1}-{year}-3"


def _create_course_for_training(user, title, description=''):
    """为新建项目自动在 MySQL course 表创建课程记录"""
    teacher = _get_teacher_info(user['id'])
    db = get_mysql_db()
    school_id = _get_fallback_school_id()
    college_id = None
    teacher_name = user.get('username') or ''

    if teacher:
        teacher_name = teacher.get('name') or teacher_name
        if teacher.get('school_id'):
            school_id = teacher['school_id']
        if teacher.get('college_id'):
            college_id = teacher['college_id']

    with db.cursor() as cursor:
        course_code = _generate_course_code(title, user['id'])
        semester = _current_semester()
        cursor.execute(
            """
            INSERT INTO course (
                course_name, course_code, semester, credit,
                school_id, college_id, teacher_id, teacher_name, description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                title, course_code, semester, 0,
                school_id, college_id, user['id'], teacher_name, description
            )
        )
    db.commit()

    with db.cursor() as cursor:
        cursor.execute("SELECT LAST_INSERT_ID() AS id")
        return cursor.fetchone()['id']


def _delete_course_for_training(course_id):
    """删除项目对应的 course 记录（创建失败时回滚用）"""
    if not course_id:
        return
    db = get_mysql_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM teach WHERE course_id = %s", (int(course_id),))
        cursor.execute("DELETE FROM student_course WHERE course_id = %s", (int(course_id),))
        cursor.execute("DELETE FROM course WHERE id = %s", (int(course_id),))
    db.commit()


def _update_course_for_training(course_id, title):
    """项目标题变更时同步更新 course 表"""
    if not course_id:
        return
    db = get_mysql_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE course SET course_name = %s WHERE id = %s",
            (title, int(course_id))
        )
    db.commit()


def _reset_teach_and_enrollment(course_id, teacher_id, class_ids):
    """重置某课程的 teach 关系与学生选课，然后按 class_ids 重新建立"""
    if not course_id:
        return
    db = get_mysql_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM teach WHERE course_id = %s", (int(course_id),))
        cursor.execute("DELETE FROM student_course WHERE course_id = %s", (int(course_id),))
    db.commit()
    _sync_teach_and_enrollment(course_id, teacher_id, class_ids)


def _sync_teach_and_enrollment(course_id, teacher_id, class_ids):
    """建立 teach 关系，并为班级学生自动选课"""
    if not class_ids:
        return
    db = get_mysql_db()
    class_ids = [int(cid) for cid in class_ids]
    with db.cursor() as cursor:
        for cid in class_ids:
            try:
                cursor.execute(
                    "INSERT INTO teach (course_id, teacher_id, class_id) VALUES (%s, %s, %s)",
                    (int(course_id), int(teacher_id), cid)
                )
            except Exception:
                pass

        placeholders = ','.join(['%s'] * len(class_ids))
        cursor.execute(
            f"SELECT DISTINCT id AS student_id FROM students "
            f"WHERE class_id IN ({placeholders}) AND is_active = 1",
            tuple(class_ids)
        )
        students = cursor.fetchall()
        for stu in students:
            try:
                cursor.execute(
                    "INSERT INTO student_course (student_id, course_id) VALUES (%s, %s)",
                    (stu['student_id'], int(course_id))
                )
            except Exception:
                pass
    db.commit()


def _get_class_names(class_ids):
    """从 MySQL 查询班级名称，返回 {class_id: class_name}"""
    if not class_ids:
        return {}
    db = get_mysql_db()
    names = {}
    with db.cursor() as mc:
        placeholders = ','.join(['%s'] * len(class_ids))
        mc.execute(
            f"SELECT id, class_name FROM classes WHERE id IN ({placeholders}) AND is_active = 1",
            tuple(int(cid) for cid in class_ids)
        )
        for row in mc.fetchall():
            names[row['id']] = row['class_name']
    return names


def _set_training_classes(cursor, training_id, class_ids):
    """全量替换实训的班级绑定"""
    cursor.execute('DELETE FROM training_classes WHERE training_id = ?', (int(training_id),))
    if not class_ids:
        return
    class_ids = [int(cid) for cid in class_ids]
    names = _get_class_names(class_ids)
    for cid in class_ids:
        cursor.execute('''
            INSERT INTO training_classes (training_id, class_id, class_name, created_at)
            VALUES (?, ?, ?, ?)
        ''', (int(training_id), cid, names.get(cid, ''), now_str()))


def _get_training_classes(cursor, training_id):
    """返回实训绑定的班级 ID 与名称列表"""
    cursor.execute(
        'SELECT class_id, class_name FROM training_classes WHERE training_id = ?',
        (int(training_id),)
    )
    rows = cursor.fetchall()
    class_ids = [r['class_id'] for r in rows]
    class_names = [r['class_name'] for r in rows if r['class_name']]
    return class_ids, class_names


def _enrich_training(cursor, t):
    """给实训对象补充班级绑定、提交统计等展示字段"""
    class_ids, class_names = _get_training_classes(cursor, t['id'])
    t['assignedClassIds'] = class_ids
    t['assignedClasses'] = class_names
    cursor.execute('SELECT COUNT(*) FROM submissions WHERE training_id = ?', (t['id'],))
    t['submission_count'] = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM submissions WHERE training_id = ? AND status = ?', (t['id'], 'evaluated'))
    t['evaluated_count'] = cursor.fetchone()[0]
    cursor.execute('SELECT final_score FROM submissions WHERE training_id = ? AND final_score IS NOT NULL', (t['id'],))
    scores = [r[0] for r in cursor.fetchall()]
    t['avg_score'] = round(sum(scores) / len(scores), 1) if scores else 0.0
    # 从 course 表读取课程名称作为项目展示名
    course_id = t.get('course_id') or 0
    if course_id:
        try:
            db = get_mysql_db()
            with db.cursor() as mc:
                mc.execute('SELECT course_name FROM course WHERE id = %s', (int(course_id),))
                row = mc.fetchone()
                if row and row.get('course_name'):
                    t['courseName'] = row['course_name']
        except Exception:
            t['courseName'] = t.get('course_name') or t.get('title') or ''
    if not t.get('courseName'):
        t['courseName'] = t.get('course_name') or t.get('title') or ''
    # 兼容前端字段名
    t['deadline'] = t.get('deadline') or ''
    t['documentUrl'] = t.get('document_url') or ''
    t['codeStandard'] = t.get('code_standard') or ''
    t['dimensions'] = parse_json_field(t.get('dimensions'), [])
    return t

def handle_student_my_projects(handler):
    """学生查看自己参与的所有实训项目（通过course关联）"""
    user, err = require_user(handler)
    if err:
        return err
    if not is_student(user):
        return forbidden('仅学生可访问')

    # 获取学生加入的课程ID列表
    course_ids = get_student_course_ids(user['id'])
    if not course_ids:
        return 200, [('Content-Type', 'application/json')], json.dumps([], ensure_ascii=False)

    # 查询这些课程对应的实训项目
    conn = get_sqlite_db()
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(course_ids))
    cursor.execute(
        f'SELECT * FROM trainings WHERE course_id IN ({placeholders}) ORDER BY updated_at DESC',
        tuple(course_ids)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        t = _enrich_training(cursor, dict_from_row(row))
        # 检查学生是否已提交
        cursor.execute(
            'SELECT id, final_score, status FROM submissions WHERE training_id = ? AND student_id = ? ORDER BY created_at DESC LIMIT 1',
            (t['id'], user.get('username', ''))
        )
        sub = cursor.fetchone()
        if sub:
            t['hasSubmitted'] = True
            t['final_score'] = sub['final_score']
            t['submission_status'] = sub['status']
        else:
            t['hasSubmitted'] = False
            t['final_score'] = None
            t['submission_status'] = None
        result.append(t)

    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)


def handle_student_my_submissions(handler):
    """学生查看自己的全部提交记录"""
    return handle_student_submissions(handler)


def handle_list_trainings(handler):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    conn = get_db()
    cursor = conn.cursor()

    if auth.is_admin(user):
        cursor.execute('SELECT * FROM trainings ORDER BY updated_at DESC')
    else:
        course_ids = auth.get_teacher_course_ids(user['id'])
        if not course_ids:
            return 200, [('Content-Type', 'application/json')], json.dumps([], ensure_ascii=False)
        placeholders = ','.join(['?'] * len(course_ids))
        cursor.execute(
            f'SELECT * FROM trainings WHERE course_id IN ({placeholders}) ORDER BY updated_at DESC',
            tuple(course_ids)
        )

    rows = cursor.fetchall()
    result = []
    for row in rows:
        t = _enrich_training(cursor, dict_from_row(row))
        result.append(t)
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)

def handle_get_training(handler, training_id):
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '实训项目不存在'}, ensure_ascii=False)
    t = _enrich_training(cursor, dict_from_row(row))
    return 200, [('Content-Type', 'application/json')], json.dumps(t, ensure_ascii=False)

def handle_create_training(handler):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    data = handler.parse_json_body()
    valid, errors = validate_training_create(data)
    if not valid:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': errors}, ensure_ascii=False)

    course_id = data.get('course_id')
    auto_created_course_id = None
    if course_id is not None and course_id != '':
        # 兼容旧模式：显式传入了已有课程 ID
        course_id = int(course_id)
        if not auth.can_access_course(user, course_id):
            return auth.forbidden('您无权在该课程下创建实训')
    else:
        # 新模式：项目即课程，自动创建 course 记录
        try:
            course_id = _create_course_for_training(
                user, data.get('title', ''), data.get('description', '')
            )
            auto_created_course_id = course_id
        except Exception as e:
            return 500, [('Content-Type', 'application/json')], json.dumps(
                {'detail': f'创建课程记录失败: {str(e)}'}, ensure_ascii=False)

    status = data.get('status', 'not_started')
    if status not in TRAINING_STATUSES:
        status = 'not_started'

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO trainings (title, description, course_name, teacher_name, course_id,
                                  expected_steps, expected_outcomes, deadline, dimensions,
                                  document_url, code_standard, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title'), data.get('description'), data.get('course_name'), data.get('teacher_name'),
            course_id, data.get('expected_steps'), data.get('expected_outcomes'),
            data.get('deadline'), serialize_json_field(data.get('dimensions', [])),
            data.get('document_url'), data.get('code_standard'), status,
            now_str(), now_str()
        ))
        conn.commit()
        training_id = cursor.lastrowid
    except Exception as e:
        # SQLite 写入失败时回滚自动创建的 course 记录
        if auto_created_course_id:
            _delete_course_for_training(auto_created_course_id)
        raise

    # 班级绑定（SQLite）
    class_ids = data.get('class_ids', [])
    if class_ids:
        _set_training_classes(cursor, training_id, class_ids)
        conn.commit()

    # MySQL teach 关系与学生选课
    if class_ids:
        try:
            _sync_teach_and_enrollment(course_id, user['id'], class_ids)
        except Exception as e:
            # 关系同步失败记录日志，但不影响项目创建主流程
            print(f"[warning] 项目 {training_id} 同步 teach/student_course 失败: {e}")

    record_operation_log('training_create', handler.headers.get('X-User-Name', 'system'), data.get('title', ''))
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    t = _enrich_training(cursor, dict_from_row(cursor.fetchone()))
    return 200, [('Content-Type', 'application/json')], json.dumps(t, ensure_ascii=False)

def handle_update_training(handler, training_id):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    data = handler.parse_json_body()
    valid, errors = validate_training_update(data)
    if not valid:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': errors}, ensure_ascii=False)

    course_id = data.get('course_id')
    if course_id is not None:
        course_id = int(course_id)
        if not auth.can_access_course(user, course_id):
            return auth.forbidden('您无权将实训归属到该课程')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    existing = cursor.fetchone()
    if not existing:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '实训项目不存在'}, ensure_ascii=False)
    existing_course_id = existing['course_id']

    field_map = {
        'title': 'title', 'description': 'description', 'course_name': 'course_name',
        'teacher_name': 'teacher_name', 'course_id': 'course_id',
        'expected_steps': 'expected_steps', 'expected_outcomes': 'expected_outcomes',
        'deadline': 'deadline', 'dimensions': 'dimensions',
        'document_url': 'document_url', 'code_standard': 'code_standard',
        'status': 'status'
    }
    fields = []
    values = []
    for k, col in field_map.items():
        if k in data:
            fields.append(f"{col} = ?")
            if k == 'dimensions':
                values.append(serialize_json_field(data[k]))
            else:
                values.append(data[k])
    values.append(now_str())
    fields.append("updated_at = ?")
    values.append(training_id)
    cursor.execute(f'UPDATE trainings SET {", ".join(fields)} WHERE id = ?', values)

    # 班级绑定
    if 'class_ids' in data:
        _set_training_classes(cursor, training_id, data['class_ids'])

    conn.commit()

    # 同步更新 course 表
    if 'title' in data and existing_course_id:
        try:
            _update_course_for_training(existing_course_id, data['title'])
        except Exception as e:
            print(f"[warning] 项目 {training_id} 同步 course 名称失败: {e}")

    if 'class_ids' in data and existing_course_id:
        try:
            _reset_teach_and_enrollment(existing_course_id, user['id'], data['class_ids'])
        except Exception as e:
            print(f"[warning] 项目 {training_id} 重置 teach/student_course 失败: {e}")

    record_operation_log('training_update', handler.headers.get('X-User-Name', 'system'), f'id={training_id}')
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    t = _enrich_training(cursor, dict_from_row(cursor.fetchone()))
    return 200, [('Content-Type', 'application/json')], json.dumps(t, ensure_ascii=False)

def handle_upload_training_document(handler, path):
    """上传实训任务文档，保存到 uploads/training_{id}/ 并更新 document_url"""
    training_id = int(re.search(r'/api/training/(\d+)/document', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    data, files = handler.parse_form_body()
    if not files:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '请选择要上传的文档'}, ensure_ascii=False)

    # 只取第一个文件
    fname, content = next(iter(files.items()))
    ext = os.path.splitext(fname)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': f'不支持的文件格式: {ext}'}, ensure_ascii=False)

    max_upload_size_mb = get_system_config_int('upload_max_size_mb', 50)
    max_upload_size = max_upload_size_mb * 1024 * 1024
    if len(content) > max_upload_size:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': f'文件大小超过{max_upload_size_mb}MB限制'}, ensure_ascii=False)

    sub_dir = f"training_{training_id}"
    dir_path = os.path.join(UPLOAD_DIR, sub_dir)
    os.makedirs(dir_path, exist_ok=True)

    base, ext = os.path.splitext(fname)
    filepath = os.path.join(dir_path, fname)
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(dir_path, f"{base}_{counter}{ext}")
        counter += 1
    with open(filepath, 'wb') as f:
        f.write(content)

    document_url = f"/uploads/{sub_dir}/{os.path.basename(filepath)}".replace('\\', '/')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE trainings SET document_url = ?, updated_at = ? WHERE id = ?',
                   (document_url, now_str(), training_id))
    conn.commit()
    record_operation_log('training_upload_doc', handler.headers.get('X-User-Name', 'system'), f'id={training_id}')

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'document_url': document_url,
        'filename': os.path.basename(filepath),
        'size': len(content)
    }, ensure_ascii=False)

def handle_delete_training(handler, training_id):
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    existing = cursor.fetchone()
    if not existing:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '实训项目不存在'}, ensure_ascii=False)
    course_id = existing['course_id']
    cursor.execute('DELETE FROM trainings WHERE id = ?', (training_id,))
    conn.commit()

    # 同步将对应 course 标记为禁用，保持 course 表与项目一致
    if course_id:
        try:
            db = get_mysql_db()
            with db.cursor() as cursor_mysql:
                cursor_mysql.execute(
                    "UPDATE course SET is_active = 0 WHERE id = %s",
                    (int(course_id),)
                )
            db.commit()
        except Exception as e:
            print(f"[warning] 删除项目 {training_id} 同步禁用 course {course_id} 失败: {e}")

    record_operation_log('training_delete', handler.headers.get('X-User-Name', 'system'), f'id={training_id}')
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '删除成功'}, ensure_ascii=False)

def handle_list_submissions(handler, path):
    training_id = int(re.search(r'/api/training/(\d+)/submissions', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE training_id = ? ORDER BY created_at DESC', (training_id,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        s = dict_from_row(row)
        s['files'] = parse_json_field(s['files'], [])
        s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
        result.append(s)
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)


def handle_student_submissions(handler):
    """学生查看自己的全部提交记录（仅返回当前学生）"""
    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_student(user):
        return auth.forbidden('仅学生可访问')

    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT student_no, name FROM students WHERE id = %s AND is_active = 1",
            (int(user['id']),)
        )
        stu = mc.fetchone()
    if not stu:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '学生信息不存在'}, ensure_ascii=False)

    student_no = stu['student_no']
    student_name = stu['name']

    conn = get_db()
    cursor = conn.cursor()
    # 仅按学号匹配，避免同名学生越权
    cursor.execute(
        "SELECT * FROM submissions WHERE student_id = ? ORDER BY created_at DESC",
        (student_no,)
    )
    rows = cursor.fetchall()
    result = []
    for row in rows:
        s = dict_from_row(row)
        s['files'] = parse_json_field(s['files'], [])
        s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
        # 补充实训标题
        cursor.execute('SELECT title FROM trainings WHERE id = ?', (s['training_id'],))
        t = cursor.fetchone()
        s['training_title'] = t[0] if t else ''
        s['student_name'] = student_name
        result.append(s)
    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'total': len(result), 'submissions': result}, ensure_ascii=False)

def handle_submit_work(handler, path):
    training_id = int(re.search(r'/api/training/(\d+)/submit', path).group(1))
    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_student(user):
        return auth.forbidden('仅学生可提交作业')

    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    if get_system_config_int('enable_submission', 1) == 0:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '当前系统已关闭学生提交功能'}, ensure_ascii=False)

    # 从登录态推导学生身份，防止表单伪造
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT student_no, name FROM students WHERE id = %s AND is_active = 1",
            (int(user['id']),)
        )
        stu = mc.fetchone()
    if not stu:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '学生信息不存在'}, ensure_ascii=False)
    student_no = stu['student_no']
    student_name = stu['name']

    data, files = handler.parse_form_body()
    # 覆盖表单中的身份信息
    data['student_id'] = student_no
    data['student_name'] = student_name

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    if not cursor.fetchone():
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '实训项目不存在'}, ensure_ascii=False)
    if not data.get('student_name'):
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '学生姓名不能为空'}, ensure_ascii=False)
    saved_files = []
    parsed_content = ""
    if files:
        sub_dir = f"training_{training_id}"
        dir_path = os.path.join(UPLOAD_DIR, sub_dir)
        os.makedirs(dir_path, exist_ok=True)
        max_upload_size_mb = get_system_config_int('upload_max_size_mb', 50)
        max_upload_size = max_upload_size_mb * 1024 * 1024
        for fname, content in files.items():
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return 400, [('Content-Type', 'application/json')], json.dumps({'detail': f'不支持的文件格式: {ext}'}, ensure_ascii=False)
            if len(content) > max_upload_size:
                return 400, [('Content-Type', 'application/json')], json.dumps({'detail': f'文件大小超过{max_upload_size_mb}MB限制'}, ensure_ascii=False)
            base, ext = os.path.splitext(fname)
            filepath = os.path.join(dir_path, fname)
            counter = 1
            while os.path.exists(filepath):
                filepath = os.path.join(dir_path, f"{base}_{counter}{ext}")
                counter += 1
            with open(filepath, 'wb') as f:
                f.write(content)
            saved_files.append({'filename': fname, 'path': filepath, 'size': len(content)})
            if ext in ['.txt', '.csv']:
                try:
                    text = content.decode('utf-8')
                    parsed_content += f"\n=== {fname} ===\n{text[:5000]}\n"
                except:
                    pass
            else:
                parsed_content += f"\n【{fname}】(非文本文件，需安装对应库才能解析)\n"
    # 从 MySQL 查询学生班级信息，写入 SQLite submissions 以便按班级筛选/展示
    class_id = 0
    class_name = ''
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT class_id, class_name FROM students WHERE student_no = %s AND is_active = 1",
            (student_no,)
        )
        stu = mc.fetchone()
        if stu:
            class_id = stu['class_id'] or 0
            class_name = stu['class_name'] or ''

    cursor.execute('''
        INSERT INTO submissions (training_id, student_name, student_id, class_id, class_name, files, parsed_content, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (training_id, data.get('student_name'), data.get('student_id', ''),
          class_id, class_name,
          json.dumps(saved_files, ensure_ascii=False), parsed_content.strip(), 'submitted', now_str(), now_str()))
    conn.commit()
    submission_id = cursor.lastrowid

    # 同步写入 submit_work（MySQL 信息库）以便教师端查询
    _sync_to_submit_work(training_id, data, saved_files, cursor)

    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    s = dict_from_row(cursor.fetchone())
    s['files'] = parse_json_field(s['files'], [])
    s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
    return 200, [('Content-Type', 'application/json')], json.dumps(s, ensure_ascii=False)

def _sync_to_submit_work(training_id, data, saved_files, cursor_sqlite):
    """将新提交的作业同步写入 MySQL submit_work 表（教师端可查）"""
    import time

    student_no = data.get('student_id', '')
    student_name = data.get('student_name', '')

    if not student_no:
        return

    # 从 MySQL students 表查 class_id / class_name
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT id, class_id, class_name FROM students WHERE student_no = %s AND is_active = 1",
            (student_no,)
        )
        stu = mc.fetchone()

    if not stu:
        return  # 学生不在信息库，跳过

    mysql_student_id = stu['id']
    class_id = stu['class_id'] if stu['class_id'] else 0
    class_name = stu['class_name'] or ''

    # 查实训标题和 course_id
    cursor_sqlite.execute('SELECT title, course_id FROM trainings WHERE id = ?', (training_id,))
    t = cursor_sqlite.fetchone()
    training_title = t['title'] if t else ''
    course_id = t['course_id'] if t and t['course_id'] else 0

    # 写入 submit_work
    from config import UPLOAD_HOMEWORK_DIR

    with mysql_db.cursor() as mc:
        for sf in saved_files:
            fname = sf['filename']
            filepath = sf['path']
            fsize = sf['size']
            ext = os.path.splitext(fname)[1].lower()

            # 重新在 homework 目录存一份
            sub_dir = os.path.join(str(class_id), str(training_id))
            full_dir = os.path.join(UPLOAD_HOMEWORK_DIR, sub_dir)
            os.makedirs(full_dir, exist_ok=True)

            timestamp = int(time.time())
            safe_name = f'{student_no}_{timestamp}{ext}'
            dest_path = os.path.join(full_dir, safe_name)

            if os.path.exists(filepath):
                with open(filepath, 'rb') as src_f:
                    with open(dest_path, 'wb') as dst_f:
                        dst_f.write(src_f.read())

            relative_path = os.path.join(sub_dir, safe_name).replace('\\', '/')

            from datetime import datetime
            mc.execute(
                "INSERT INTO submit_work (student_id, student_no, student_name, class_id, class_name, "
                "training_id, course_id, training_title, file_path, file_original_name, file_extension, "
                "file_size, content_type, submitted_at) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    mysql_student_id, student_no, student_name, class_id, class_name,
                    training_id, course_id, training_title, relative_path, fname, ext,
                    fsize, 'application/octet-stream',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
    mysql_db.commit()


def handle_get_submission(handler, submission_id):
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '提交不存在'}, ensure_ascii=False)
    s = dict_from_row(row)
    s['files'] = parse_json_field(s['files'], [])
    s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
    return 200, [('Content-Type', 'application/json')], json.dumps(s, ensure_ascii=False)

def handle_delete_submission(handler, submission_id):
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    if not cursor.fetchone():
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '提交不存在'}, ensure_ascii=False)
    cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
    conn.commit()
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '删除成功'}, ensure_ascii=False)