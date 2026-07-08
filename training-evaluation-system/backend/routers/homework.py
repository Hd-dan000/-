# -*- coding: utf-8 -*-
"""作业提交与查看模块
- 学生上传：POST /api/homework/upload
- 教师端查询本班作业：GET /api/homework/teacher/submissions
- 教师评分评语：PUT /api/homework/review/<id>
- 文件在线预览/下载：GET /api/homework/file/<id>
- 教师班级列表：GET /api/teacher/classes （已有）
"""
import json
import os
import re
import time
import mimetypes

from database_mysql import get_db as get_mysql_db
from database import get_db as get_sqlite_db
from routers import auth


def _get_mysql_cursor():
    db = get_mysql_db()
    return db, db.cursor()


def _now():
    """返回 MySQL NOW() 兼容的格式"""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ============================================================
# 学生上传作业
# POST /api/homework/upload
# ============================================================
def handle_homework_upload(handler):
    """学生上传作业文件
    参数（multipart/form-data）：
      - training_id: 实训任务ID
      - file: 作业文件（.pdf / .doc / .docx / .mp4）
    学生身份从登录态推导，防止伪造他人提交。
    """
    from config import UPLOAD_HOMEWORK_DIR, ALLOWED_HOMEWORK_EXTENSIONS, MAX_HOMEWORK_SIZE

    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_student(user):
        return auth.forbidden('仅学生可上传作业')

    data, files = handler.parse_form_body()
    training_id = data.get('training_id', '').strip()
    if not training_id:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少必填字段 training_id'}, ensure_ascii=False
        )

    # 从登录态推导学生身份
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT id, student_no, name, class_id, class_name FROM students WHERE id = %s AND is_active = 1",
            (int(user['id']),)
        )
        stu = mc.fetchone()
    if not stu:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '学生信息不存在'}, ensure_ascii=False
        )

    student_id = stu['id']
    student_no = stu['student_no']
    student_name = stu['name']
    class_id = stu['class_id'] if stu['class_id'] else 0
    class_name = stu['class_name'] or ''

    # 校验学生是否加入了该实训所属课程
    sqlite_db = get_sqlite_db()
    sqlite_cursor = sqlite_db.cursor()
    sqlite_cursor.execute('SELECT course_id, title FROM trainings WHERE id = ?', (int(training_id),))
    training_row = sqlite_cursor.fetchone()
    if not training_row or not training_row[0]:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '实训任务未关联课程，无法提交'}, ensure_ascii=False
        )
    course_id = training_row[0]
    training_title = training_row[1] or ''

    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT id FROM student_course WHERE student_id = %s AND course_id = %s",
            (int(student_id), int(course_id))
        )
        if not mc.fetchone():
            return 403, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '您未加入该实训所属课程，无法提交'}, ensure_ascii=False
            )

    if not files:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '请选择要上传的文件'}, ensure_ascii=False
        )

    # 只处理传入的第一个文件
    fname = list(files.keys())[0]
    content = files[fname]

    ext = os.path.splitext(fname)[1].lower()
    if ext not in ALLOWED_HOMEWORK_EXTENSIONS:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'不支持的文件格式: {ext}，仅支持 .pdf .doc .docx .mp4'},
            ensure_ascii=False
        )

    if len(content) > MAX_HOMEWORK_SIZE:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': f'文件大小超过限制（最大100MB）'},
            ensure_ascii=False
        )

    # 保存到磁盘：upload/homework/{class_id}/{student_no}_{timestamp}{ext}
    sub_dir = os.path.join(str(class_id), str(training_id))
    full_dir = os.path.join(UPLOAD_HOMEWORK_DIR, sub_dir)
    os.makedirs(full_dir, exist_ok=True)

    timestamp = int(time.time())
    safe_name = f'{student_no}_{timestamp}{ext}'
    dest_path = os.path.join(full_dir, safe_name)

    with open(dest_path, 'wb') as f:
        f.write(content)

    # 相对路径（相对 upload/homework）
    relative_path = os.path.join(sub_dir, safe_name).replace('\\', '/')

    # 写入 MySQL submit_work 表
    db, cursor = _get_mysql_cursor()
    try:
        cursor.execute(
            "INSERT INTO submit_work (student_id, student_no, student_name, class_id, class_name, "
            "training_id, training_title, file_path, file_original_name, file_extension, "
            "file_size, content_type, submitted_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                int(student_id), student_no, student_name, int(class_id), class_name,
                int(training_id), training_title, relative_path, fname, ext,
                len(content), mimetypes.guess_type(fname)[0] or 'application/octet-stream',
                _now()
            )
        )
        db.commit()
        work_id = cursor.lastrowid
    finally:
        cursor.close()

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'message': '作业提交成功',
        'work_id': work_id,
        'file': {
            'original_name': fname,
            'size': len(content),
            'path': relative_path,
        }
    }, ensure_ascii=False)


# ============================================================
# 教师查询本班学生作业
# GET /api/homework/teacher/submissions?class_id=xxx&training_id=xxx
# ============================================================
def handle_teacher_submissions(handler):
    """教师查询所教班级的作业提交记录
    可选参数：
      - class_id: 按班级筛选
      - training_id: 按实训任务筛选
    自动根据登录教师 ID 过滤其授课班级
    """
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)

    teacher_id = user['id']

    # 获取该教师的授课班级ID列表
    db, cursor = _get_mysql_cursor()
    try:
        cursor.execute(
            "SELECT class_id FROM teacherclasses WHERE teacher_id = %s",
            (teacher_id,)
        )
        teacher_class_ids = [row['class_id'] for row in cursor.fetchall()]

        if not teacher_class_ids:
            return 200, [('Content-Type', 'application/json')], json.dumps({
                'total': 0,
                'submissions': []
            }, ensure_ascii=False)

        # 构建 WHERE 条件
        where_clauses = [f"sw.class_id IN ({','.join(str(cid) for cid in teacher_class_ids)})"]

        class_id_param = query.get('class_id', [None])[0]
        training_id_param = query.get('training_id', [None])[0]

        params = []
        if class_id_param:
            where_clauses.append("sw.class_id = %s")
            params.append(int(class_id_param))
        if training_id_param:
            where_clauses.append("sw.training_id = %s")
            params.append(int(training_id_param))

        where_sql = ' AND '.join(where_clauses)

        cursor.execute(f"""
            SELECT sw.*, tc.teacher_id 
            FROM submit_work sw
            JOIN teacherclasses tc ON tc.class_id = sw.class_id AND tc.teacher_id = %s
            WHERE {where_sql}
            ORDER BY sw.submitted_at DESC
        """, (teacher_id, *params))

        rows = cursor.fetchall()
        submissions = []
        for row in rows:
            item = dict(row)
            # 时间对象转字符串
            for key in ('submitted_at', 'reviewed_at'):
                if key in item and item[key] is not None:
                    item[key] = item[key].strftime('%Y-%m-%d %H:%M:%S') if hasattr(item[key], 'strftime') else str(item[key])
            if 'teacher_score' in item and item['teacher_score'] is not None:
                item['teacher_score'] = float(item['teacher_score'])
            submissions.append(item)

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'total': len(submissions),
            'class_ids': teacher_class_ids,
            'submissions': submissions
        }, ensure_ascii=False, default=str)

    finally:
        cursor.close()


# ============================================================
# 教师获取自己授课班级列表（带学生数）
# GET /api/homework/teacher/class-list
# ============================================================
def handle_teacher_class_list(handler):
    """教师获取自己授课的班级列表及学生人数"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    teacher_id = user['id']

    db, cursor = _get_mysql_cursor()
    try:
        cursor.execute("""
            SELECT c.id, c.class_code, c.class_name, c.major, c.grade,
                   (SELECT COUNT(*) FROM students s WHERE s.class_id = c.id AND s.is_active = 1) as student_count
            FROM teacherclasses tc
            JOIN classes c ON c.id = tc.class_id
            WHERE tc.teacher_id = %s AND c.is_active = 1
            ORDER BY c.class_name
        """, (teacher_id,))
        classes = []
        for row in cursor.fetchall():
            row = dict(row)
            classes.append(row)

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'total_classes': len(classes),
            'classes': classes
        }, ensure_ascii=True)

    finally:
        cursor.close()


# ============================================================
# 教师获取有提交记录的实训任务列表
# GET /api/homework/teacher/trainings?class_id=xxx
# ============================================================
def handle_teacher_training_list(handler):
    """教师获取有作业提交记录的实训任务"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)

    teacher_id = user['id']
    class_id = query.get('class_id', [None])[0]

    db, cursor = _get_mysql_cursor()
    try:
        cursor.execute(
            "SELECT class_id FROM teacherclasses WHERE teacher_id = %s", (teacher_id,)
        )
        teacher_class_ids = [row['class_id'] for row in cursor.fetchall()]
        if not teacher_class_ids:
            return 200, [('Content-Type', 'application/json')], json.dumps({'total': 0, 'trainings': []}, ensure_ascii=False)

        where = [f"class_id IN ({','.join(str(c) for c in teacher_class_ids)})"]
        params = []
        if class_id:
            where.append("class_id = %s")
            params.append(int(class_id))

        cursor.execute(f"""
            SELECT training_id, training_title, class_id, class_name, COUNT(*) as submit_count,
                   MAX(submitted_at) as last_submit
            FROM submit_work
            WHERE {' AND '.join(where)}
            GROUP BY training_id, training_title, class_id, class_name
            ORDER BY last_submit DESC
        """, params)

        trainings = []
        for row in cursor.fetchall():
            item = dict(row)
            if 'last_submit' in item and item['last_submit'] is not None:
                item['last_submit'] = item['last_submit'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(item['last_submit'], 'strftime') else str(item['last_submit'])
            trainings.append(item)

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'total': len(trainings),
            'trainings': trainings
        }, ensure_ascii=False, default=str)

    finally:
        cursor.close()


# ============================================================
# 教师评分评语
# PUT /api/homework/review/<id>
# ============================================================
def handle_teacher_review(handler, work_id):
    """教师给作业打分和评语"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    teacher_id = user['id']
    data = handler.parse_json_body()
    teacher_score = data.get('teacher_score')
    teacher_comment = data.get('teacher_comment', '')

    if teacher_score is not None:
        try:
            teacher_score = float(teacher_score)
            if teacher_score < 0 or teacher_score > 100:
                raise ValueError
        except (ValueError, TypeError):
            return 400, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '评分必须在0-100之间'}, ensure_ascii=False
            )

    db, cursor = _get_mysql_cursor()
    try:
        # 检查作业是否存在并且属于该教师的班级
        cursor.execute("""
            SELECT sw.id FROM submit_work sw
            JOIN teacherclasses tc ON tc.class_id = sw.class_id AND tc.teacher_id = %s
            WHERE sw.id = %s
        """, (teacher_id, int(work_id)))
        if not cursor.fetchone():
            return 404, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '作业不存在或不属于您的班级'}, ensure_ascii=False
            )

        updates = []
        params = []
        if teacher_score is not None:
            updates.append("teacher_score = %s")
            params.append(teacher_score)
        if teacher_comment:
            updates.append("teacher_comment = %s")
            params.append(teacher_comment)

        updates.append("status = 'evaluated'")
        updates.append("reviewed_at = %s")
        params.append(_now())

        params.append(int(work_id))
        cursor.execute(
            f"UPDATE submit_work SET {', '.join(updates)} WHERE id = %s",
            params
        )
        db.commit()

        return 200, [('Content-Type', 'application/json')], json.dumps({
            'message': '评分成功',
            'work_id': int(work_id),
            'teacher_score': teacher_score,
        }, ensure_ascii=False)
    finally:
        cursor.close()


# ============================================================
# 文件在线预览/下载
# GET /api/homework/file/<id>
# ============================================================
def handle_serve_homework_file(handler, work_id):
    """提供作业文件的在线预览或下载"""
    from config import UPLOAD_HOMEWORK_DIR

    user, err = auth.require_user(handler)
    if err:
        return err

    db, cursor = _get_mysql_cursor()
    try:
        cursor.execute(
            "SELECT sw.file_path, sw.file_original_name, sw.file_extension, sw.student_id, sw.class_id "
            "FROM submit_work sw WHERE sw.id = %s",
            (int(work_id),)
        )
        row = cursor.fetchone()
        if not row:
            return 404, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '文件记录不存在'}, ensure_ascii=False
            )

        # 学生只能访问自己的作业；教师可访问其授课班级的作业；管理员直接放行
        if auth.is_student(user):
            if int(row['student_id']) != int(user['id']):
                return auth.forbidden('无权访问该文件')
        elif auth.is_teacher(user):
            cursor.execute(
                "SELECT 1 FROM teacherclasses WHERE teacher_id = %s AND class_id = %s",
                (int(user['id']), int(row['class_id']))
            )
            if not cursor.fetchone():
                return auth.forbidden('无权访问该文件')
        elif not auth.is_admin(user):
            return auth.forbidden('无权访问该文件')

        cursor.execute(
            "SELECT file_path, file_original_name, file_extension FROM submit_work WHERE id = %s",
            (int(work_id),)
        )
        row = cursor.fetchone()
        if not row:
            return 404, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '文件记录不存在'}, ensure_ascii=False
            )

        file_path = row['file_path']
        original_name = row['file_original_name']
        ext = row['file_extension']

        full_path = os.path.join(UPLOAD_HOMEWORK_DIR, file_path)
        if not os.path.exists(full_path):
            return 404, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '文件不存在于磁盘'}, ensure_ascii=False
            )

        # 确定 MIME 类型
        mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.mp4': 'video/mp4',
        }
        content_type = mime_map.get(ext, 'application/octet-stream')

        is_viewable = ext in ('.pdf', '.mp4')
        disposition = 'inline' if is_viewable else 'attachment'

        with open(full_path, 'rb') as f:
            content = f.read()

        return 200, [
            ('Content-Type', content_type),
            ('Content-Length', str(len(content))),
            ('Content-Disposition', f'{disposition}; filename="{original_name}"'),
            ('Accept-Ranges', 'bytes'),
            ('Access-Control-Allow-Origin', '*'),
        ], content
    finally:
        cursor.close()
