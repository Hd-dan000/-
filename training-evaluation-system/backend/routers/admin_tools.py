import json
import os

from database import get_db, dict_from_row
from database_mysql import get_db as get_mysql_db
from services.maintenance_service import build_backup_package, list_operation_logs, record_operation_log


def _require_super_admin(handler):
    if handler.headers.get('X-User-Role', '') != 'super_admin':
        return False, (403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权限，仅超级管理员可操作'}, ensure_ascii=False))
    return True, None


def _require_teacher_or_admin(handler):
    user_type = handler.headers.get('X-User-Type', '')
    user_role = handler.headers.get('X-User-Role', '')
    if user_type not in ('teacher', 'admin') and user_role not in ('teacher', 'admin', 'super_admin'):
        return False, (403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权限，仅教师或管理员可访问'}, ensure_ascii=False))
    return True, None


def handle_class_stats(handler):
    allowed, response = _require_super_admin(handler)
    if not allowed:
        return response

    sqlite_conn = get_db()
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute('SELECT student_id, final_score, status, training_id FROM submissions')
    submissions = [dict_from_row(row) for row in sqlite_cursor.fetchall()]

    mysql_conn = get_mysql_db()
    mysql_cursor = mysql_conn.cursor()
    mysql_cursor.execute('SELECT student_no, name, class_name, major, is_active FROM students WHERE is_active = 1')
    students = [dict_from_row(row) for row in mysql_cursor.fetchall()]

    student_map = {student['student_no']: student for student in students}
    class_map = {}
    for student in students:
        class_name = student.get('class_name') or '未分班'
        class_map.setdefault(class_name, {
            'class_name': class_name,
            'student_count': 0,
            'submission_count': 0,
            'evaluated_count': 0,
            'score_sum': 0.0,
            'score_count': 0,
            'avg_score': 0.0,
            'pass_count': 0,
            'pass_rate': 0.0,
            'students': [],
        })
        class_map[class_name]['student_count'] += 1
        class_map[class_name]['students'].append({
            'student_no': student['student_no'],
            'name': student['name'],
            'major': student.get('major', ''),
        })

    for submission in submissions:
        student = student_map.get(submission.get('student_id'))
        class_name = student.get('class_name') if student else '未分班'
        bucket = class_map.setdefault(class_name, {
            'class_name': class_name,
            'student_count': 0,
            'submission_count': 0,
            'evaluated_count': 0,
            'score_sum': 0.0,
            'score_count': 0,
            'avg_score': 0.0,
            'pass_count': 0,
            'pass_rate': 0.0,
            'students': [],
        })
        bucket['submission_count'] += 1
        if submission.get('status') == 'evaluated':
            bucket['evaluated_count'] += 1
        final_score = submission.get('final_score')
        if final_score is not None:
            bucket['score_sum'] += float(final_score)
            bucket['score_count'] += 1
            if float(final_score) >= 60:
                bucket['pass_count'] += 1

    class_list = []
    for item in class_map.values():
        if item['score_count'] > 0:
            item['avg_score'] = round(item['score_sum'] / item['score_count'], 1)
            item['pass_rate'] = round(item['pass_count'] * 100 / item['score_count'], 1)
        else:
            item['avg_score'] = 0.0
            item['pass_rate'] = 0.0
        item.pop('score_sum', None)
        item.pop('score_count', None)
        item.pop('pass_count', None)
        class_list.append(item)

    class_list.sort(key=lambda item: (item['avg_score'], item['submission_count']), reverse=True)

    result = {
        'total_students': len(students),
        'total_classes': len(class_list),
        'class_stats': class_list,
        'top_class': class_list[0] if class_list else None,
    }
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)


def handle_teacher_classes(handler):
    """教师端：返回当前教师授课的班级列表及统计信息。"""
    allowed, response = _require_teacher_or_admin(handler)
    if not allowed:
        return response

    teacher_id = handler.headers.get('X-User-Id', '')
    if not teacher_id:
        return 401, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '未登录或身份信息缺失'}, ensure_ascii=False)
    try:
        teacher_id = int(teacher_id)
    except ValueError:
        return 401, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无效的教师ID'}, ensure_ascii=False)

    sqlite_conn = get_db()
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute('SELECT student_id, final_score, status, training_id FROM submissions')
    submissions = [dict_from_row(row) for row in sqlite_cursor.fetchall()]

    mysql_conn = get_mysql_db()
    mysql_cursor = mysql_conn.cursor()

    # 仅查询当前教师授课的班级
    mysql_cursor.execute("""
        SELECT c.id, c.class_code, c.class_name, c.major, c.grade
        FROM teacherclasses tc
        JOIN classes c ON c.id = tc.class_id
        WHERE tc.teacher_id = %s AND c.is_active = 1
        ORDER BY c.class_name
    """, (teacher_id,))
    teacher_classes = [dict_from_row(row) for row in mysql_cursor.fetchall()]
    teacher_class_ids = [c['id'] for c in teacher_classes]

    # 仅统计这些班级里的学生
    if teacher_class_ids:
        placeholders = ','.join(['%s'] * len(teacher_class_ids))
        mysql_cursor.execute(
            f"SELECT student_no, name, class_id, class_name, major, is_active FROM students "
            f"WHERE class_id IN ({placeholders}) AND is_active = 1 ORDER BY class_name, student_no",
            tuple(teacher_class_ids)
        )
        students = [dict_from_row(row) for row in mysql_cursor.fetchall()]
    else:
        students = []

    student_map = {student['student_no']: student for student in students}
    class_map = {}
    for cls in teacher_classes:
        class_map[cls['id']] = {
            'class_name': cls['class_name'],
            'class_code': cls['class_code'],
            'major': cls.get('major', ''),
            'grade': cls.get('grade', ''),
            'student_count': 0,
            'submission_count': 0,
            'evaluated_count': 0,
            'score_sum': 0.0,
            'score_count': 0,
            'avg_score': 0.0,
            'pass_count': 0,
            'pass_rate': 0.0,
        }

    for student in students:
        class_id = student.get('class_id')
        bucket = class_map.get(class_id)
        if bucket:
            bucket['student_count'] += 1
            if not bucket['major'] and student.get('major'):
                bucket['major'] = student['major']

    for submission in submissions:
        student = student_map.get(submission.get('student_id'))
        if not student:
            continue
        class_id = student.get('class_id')
        bucket = class_map.get(class_id)
        if not bucket:
            continue
        bucket['submission_count'] += 1
        if submission.get('status') == 'evaluated':
            bucket['evaluated_count'] += 1
        final_score = submission.get('final_score')
        if final_score is not None:
            bucket['score_sum'] += float(final_score)
            bucket['score_count'] += 1
            if float(final_score) >= 60:
                bucket['pass_count'] += 1

    # 查询教师设置的开课状态
    if teacher_class_ids:
        placeholders = ','.join(['%s'] * len(teacher_class_ids))
        mysql_cursor.execute(
            f"SELECT id, teaching_status FROM classes WHERE id IN ({placeholders})",
            tuple(teacher_class_ids)
        )
        status_map = {row['id']: row['teaching_status'] for row in mysql_cursor.fetchall()}
    else:
        status_map = {}

    class_list = []
    for cls_id, item in class_map.items():
        if item['score_count'] > 0:
            item['avg_score'] = round(item['score_sum'] / item['score_count'], 1)
            item['pass_rate'] = round(item['pass_count'] * 100 / item['score_count'], 1)
        item.pop('score_sum', None)
        item.pop('score_count', None)
        item.pop('pass_count', None)
        item['teaching_status'] = status_map.get(cls_id, 'not_started')
        item['status'] = item['teaching_status']
        item['status_text'] = {
            'not_started': '未开课',
            'in_progress': '开课中',
            'ended': '已结课'
        }.get(item['teaching_status'], '未开课')
        class_list.append(item)

    class_list.sort(key=lambda x: x['class_name'])

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'total_classes': len(class_list),
        'total_students': len(students),
        'classes': class_list,
    }, ensure_ascii=False)


def handle_get_teacher_class(handler, class_id):
    """教师获取某个授课班级的详情"""
    allowed, response = _require_teacher_or_admin(handler)
    if not allowed:
        return response

    teacher_id = handler.headers.get('X-User-Id', '')
    if not teacher_id:
        return 401, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '未登录或身份信息缺失'}, ensure_ascii=False)
    try:
        teacher_id = int(teacher_id)
        class_id = int(class_id)
    except ValueError:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无效的ID'}, ensure_ascii=False)

    mysql_conn = get_mysql_db()
    with mysql_conn.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM teacherclasses WHERE teacher_id = %s AND class_id = %s LIMIT 1",
            (teacher_id, class_id)
        )
        if not cursor.fetchone():
            return 403, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '无权操作该班级'}, ensure_ascii=False)

        cursor.execute(
            "SELECT c.id, c.class_code, c.class_name, c.major, c.grade, c.teaching_status, "
            "t.name AS teacher_name FROM classes c "
            "LEFT JOIN teachers t ON t.id = %s "
            "WHERE c.id = %s AND c.is_active = 1 LIMIT 1",
            (teacher_id, class_id)
        )
        row = cursor.fetchone()
        if not row:
            return 404, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '班级不存在'}, ensure_ascii=False)

        cursor.execute(
            "SELECT COUNT(*) AS student_count FROM students WHERE class_id = %s AND is_active = 1",
            (class_id,)
        )
        student_count = cursor.fetchone()['student_count']

    teaching_status = row['teaching_status'] or 'not_started'
    result = {
        'id': row['id'],
        'class_code': row['class_code'],
        'class_name': row['class_name'],
        'major': row.get('major', ''),
        'grade': row.get('grade', ''),
        'student_count': student_count,
        'teacher_name': row.get('teacher_name', ''),
        'teaching_status': teaching_status,
        'status_text': {
            'not_started': '未开课',
            'in_progress': '开课中',
            'ended': '已结课'
        }.get(teaching_status, '未开课')
    }
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)


def handle_update_teaching_status(handler, class_id):
    """教师更新某个班级的开课状态"""
    allowed, response = _require_teacher_or_admin(handler)
    if not allowed:
        return response

    teacher_id = handler.headers.get('X-User-Id', '')
    if not teacher_id:
        return 401, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '未登录或身份信息缺失'}, ensure_ascii=False)
    try:
        teacher_id = int(teacher_id)
        class_id = int(class_id)
    except ValueError:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无效的ID'}, ensure_ascii=False)

    body = handler.parse_body_json()
    if not body or 'teaching_status' not in body:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少 teaching_status 参数'}, ensure_ascii=False)

    teaching_status = body['teaching_status']
    if teaching_status not in ('not_started', 'in_progress', 'ended'):
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无效的状态值'}, ensure_ascii=False)

    mysql_conn = get_mysql_db()
    with mysql_conn.cursor() as cursor:
        # 校验该班级是否属于当前教师
        cursor.execute(
            "SELECT 1 FROM teacherclasses WHERE teacher_id = %s AND class_id = %s LIMIT 1",
            (teacher_id, class_id)
        )
        if not cursor.fetchone():
            return 403, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '无权操作该班级'}, ensure_ascii=False)

        cursor.execute(
            "UPDATE classes SET teaching_status = %s WHERE id = %s",
            (teaching_status, class_id)
        )
        mysql_conn.commit()

    record_operation_log(
        'update_teaching_status',
        handler.headers.get('X-User-Name', handler.headers.get('X-User-Role', '')),
        f'class_id:{class_id},status:{teaching_status}'
    )

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'message': '状态更新成功'}, ensure_ascii=False)


def handle_list_logs(handler):
    allowed, response = _require_super_admin(handler)
    if not allowed:
        return response
    logs = list_operation_logs(limit=200)
    return 200, [('Content-Type', 'application/json')], json.dumps(logs, ensure_ascii=False)


def handle_backup(handler):
    allowed, response = _require_super_admin(handler)
    if not allowed:
        return response
    zip_path = build_backup_package()
    record_operation_log('backup', handler.headers.get('X-User-Name', handler.headers.get('X-User-Role', '')), os.path.basename(zip_path))
    with open(zip_path, 'rb') as f:
        content = f.read()
    return 200, [
        ('Content-Type', 'application/zip'),
        ('Content-Disposition', f'attachment; filename="{os.path.basename(zip_path)}"')
    ], content
