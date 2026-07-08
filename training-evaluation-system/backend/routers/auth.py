# -*- coding: utf-8 -*-
"""通用权限/身份校验辅助函数"""
import json

from database_mysql import get_db as get_mysql_db
from database import get_db as get_sqlite_db


def unauthorized(detail='未登录或身份信息缺失'):
    return 401, [('Content-Type', 'application/json')], json.dumps(
        {'detail': detail}, ensure_ascii=False)


def forbidden(detail='无权限访问该资源'):
    return 403, [('Content-Type', 'application/json')], json.dumps(
        {'detail': detail}, ensure_ascii=False)


def not_found(detail='资源不存在'):
    return 404, [('Content-Type', 'application/json')], json.dumps(
        {'detail': detail}, ensure_ascii=False)


def get_current_user(handler):
    """从请求头解析当前登录用户"""
    user_id = handler.headers.get('X-User-Id', '')
    if not user_id:
        return None
    try:
        user_id = int(user_id)
    except ValueError:
        return None
    return {
        'id': user_id,
        'role': handler.headers.get('X-User-Role', ''),
        'account_type': handler.headers.get('X-User-Type', ''),
        'username': handler.headers.get('X-User-Name', ''),
    }


def require_user(handler):
    user = get_current_user(handler)
    if not user:
        return None, unauthorized()
    return user, None


def is_admin(user):
    return user and user.get('role') in ('admin', 'super_admin')


def is_teacher(user):
    return user and (user.get('account_type') == 'teacher' or user.get('role') == 'teacher')


def is_student(user):
    return user and (user.get('account_type') == 'student' or user.get('role') == 'student')


def require_teacher_or_admin(handler):
    user, err = require_user(handler)
    if err:
        return None, err
    if not (is_teacher(user) or is_admin(user)):
        return None, forbidden('仅教师或管理员可访问')
    return user, None


def get_teacher_course_ids(teacher_id):
    """查询教师授课或创建的课程ID列表"""
    db = get_mysql_db()
    ids = set()
    with db.cursor() as cursor:
        cursor.execute(
            'SELECT DISTINCT course_id FROM teach WHERE teacher_id = %s',
            (teacher_id,)
        )
        for row in cursor.fetchall():
            ids.add(row['course_id'])
        cursor.execute(
            'SELECT DISTINCT id FROM course WHERE teacher_id = %s',
            (teacher_id,)
        )
        for row in cursor.fetchall():
            ids.add(row['id'])
    return list(ids)


def get_student_course_ids(student_id):
    """查询学生加入的课程ID列表"""
    db = get_mysql_db()
    with db.cursor() as cursor:
        cursor.execute(
            'SELECT course_id FROM student_course WHERE student_id = %s',
            (student_id,)
        )
        return [row['course_id'] for row in cursor.fetchall()]


def get_training_course_id(training_id):
    """获取实训所属课程ID"""
    db = get_sqlite_db()
    cursor = db.cursor()
    cursor.execute('SELECT course_id FROM trainings WHERE id = ?', (int(training_id),))
    row = cursor.fetchone()
    return row['course_id'] if row else None


def get_submission_training_id(submission_id):
    """获取提交记录所属实训ID"""
    db = get_sqlite_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT training_id FROM submissions WHERE id = ?', (int(submission_id),)
    )
    row = cursor.fetchone()
    return row['training_id'] if row else None


def get_indicator_training_id(indicator_id):
    """获取评价指标所属实训ID"""
    db = get_sqlite_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT training_id FROM evaluation_indicators WHERE id = ?', (int(indicator_id),)
    )
    row = cursor.fetchone()
    return row['training_id'] if row else None


def can_access_course(user, course_id):
    """判断用户是否有权访问某课程"""
    if not user or not course_id:
        return False
    if is_admin(user):
        return True
    cid = int(course_id)
    if is_teacher(user):
        return cid in get_teacher_course_ids(user['id'])
    if is_student(user):
        return cid in get_student_course_ids(user['id'])
    return False


def check_training_access(handler, training_id):
    """
    校验当前用户是否有权访问指定实训。
    返回 (can_access, error_response, user)
    """
    user, err = require_user(handler)
    if err:
        return False, err, None
    if is_admin(user):
        return True, None, user
    course_id = get_training_course_id(training_id)
    if course_id is None:
        return False, not_found('实训项目不存在'), user
    if can_access_course(user, course_id):
        return True, None, user
    return False, forbidden('您无权访问该实训'), user


def check_submission_access(handler, submission_id):
    """
    校验当前用户是否有权访问指定提交记录。
    返回 (can_access, error_response, user)
    """
    user, err = require_user(handler)
    if err:
        return False, err, None
    if is_admin(user):
        return True, None, user
    training_id = get_submission_training_id(submission_id)
    if training_id is None:
        return False, not_found('提交记录不存在'), user
    course_id = get_training_course_id(training_id)
    if course_id is None:
        return False, not_found('实训项目不存在'), user
    if can_access_course(user, course_id):
        return True, None, user
    return False, forbidden('您无权访问该提交记录'), user


def check_indicator_access(handler, indicator_id):
    """
    校验当前用户是否有权访问指定评价指标。
    返回 (can_access, error_response, user)
    """
    user, err = require_user(handler)
    if err:
        return False, err, None
    if is_admin(user):
        return True, None, user
    training_id = get_indicator_training_id(indicator_id)
    if training_id is None:
        return False, not_found('评价指标不存在'), user
    course_id = get_training_course_id(training_id)
    if course_id is None:
        return False, not_found('实训项目不存在'), user
    if can_access_course(user, course_id):
        return True, None, user
    return False, forbidden('您无权访问该评价指标'), user
