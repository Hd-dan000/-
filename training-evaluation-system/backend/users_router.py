"""用户管理路由 - 登录、用户 CRUD（对接信息库 admins / teachers 表）"""
import json
import hashlib
from database_mysql import get_db
from services.maintenance_service import record_operation_log


def _hash_password(password):
    """使用 SHA-256 对密码进行哈希"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def _serialize_datetimes(rows):
    for row in rows:
        for key in ('created_at', 'updated_at', 'last_login_at'):
            if key in row and row[key] is not None:
                row[key] = row[key].isoformat() if hasattr(row[key], 'isoformat') else str(row[key])


def _infer_account_type(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM admins WHERE id = %s", (user_id,))
        if cursor.fetchone():
            return 'admin'
        cursor.execute("SELECT id FROM teachers WHERE id = %s", (user_id,))
        if cursor.fetchone():
            return 'teacher'
        cursor.execute("SELECT id FROM students WHERE id = %s", (user_id,))
        if cursor.fetchone():
            return 'student'
    return None


def _find_account(username):
    """按用户名/工号查找管理员、教师或学生账号"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, display_name, role, password_hash, 'admin' AS account_type "
            "FROM admins WHERE username = %s AND is_active = 1",
            (username,),
        )
        account = cursor.fetchone()
        if account:
            return account

        cursor.execute(
            "SELECT id, teacher_no AS username, name AS display_name, "
            "'teacher' AS role, password_hash, 'teacher' AS account_type "
            "FROM teachers WHERE teacher_no = %s AND is_active = 1",
            (username,),
        )
        account = cursor.fetchone()
        if account:
            return account

        cursor.execute(
            "SELECT id, student_no AS username, name AS display_name, "
            "'student' AS role, password_hash, 'student' AS account_type "
            "FROM students WHERE student_no = %s AND is_active = 1",
            (username,),
        )
        return cursor.fetchone()


def handle_login(request_handler):
    """用户登录：管理员用用户名，教师用工号"""
    body = request_handler.parse_json_body()
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()

    if not username or not password:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '用户名和密码不能为空'}, ensure_ascii=False
        )

    user = _find_account(username)
    if not user:
        return 401, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '用户名或密码错误'}, ensure_ascii=False
        )

    if user['password_hash'] != _hash_password(password):
        return 401, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '用户名或密码错误'}, ensure_ascii=False
        )

    if user['account_type'] == 'admin':
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE admins SET last_login_at = NOW() WHERE id = %s",
                (user['id'],),
            )
        db.commit()

    record_operation_log('login', user['username'], f"{user['account_type']} 登录")

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'id': user['id'],
        'username': user['username'],
        'display_name': user['display_name'],
        'role': user['role'],
        'account_type': user['account_type'],
    }, ensure_ascii=False)


def handle_list_users(request_handler):
    """获取用户列表（仅超级管理员）"""
    auth_user = request_handler.headers.get('X-User-Role', '')
    if auth_user != 'super_admin':
        return 403, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无权限，仅超级管理员可操作'}, ensure_ascii=False
        )

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, display_name, role, '' AS phone, '' AS email, "
            "'' AS class_name, '' AS major, is_active, created_at, 'admin' AS account_type "
            "FROM admins ORDER BY created_at DESC"
        )
        admins = cursor.fetchall()
        cursor.execute(
            "SELECT id, teacher_no AS username, name AS display_name, "
            "'teacher' AS role, phone, email, '' AS class_name, '' AS major, is_active, created_at, 'teacher' AS account_type "
            "FROM teachers ORDER BY created_at DESC"
        )
        teachers = cursor.fetchall()
        cursor.execute(
            "SELECT id, student_no AS username, name AS display_name, "
            "'student' AS role, phone, email, class_name, major, is_active, created_at, 'student' AS account_type "
            "FROM students ORDER BY created_at DESC"
        )
        students = cursor.fetchall()

    users = admins + teachers + students
    _serialize_datetimes(users)
    return 200, [('Content-Type', 'application/json')], json.dumps(users, ensure_ascii=False)


def handle_create_user(request_handler):
    """创建用户（仅超级管理员）"""
    auth_user = request_handler.headers.get('X-User-Role', '')
    if auth_user != 'super_admin':
        return 403, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无权限，仅超级管理员可操作'}, ensure_ascii=False
        )

    body = request_handler.parse_json_body()
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()
    display_name = body.get('display_name', '').strip()
    role = body.get('role', 'teacher').strip()
    phone = body.get('phone', '').strip()
    email = body.get('email', '').strip()
    class_name = body.get('class_name', '').strip()
    major = body.get('major', '').strip()
    gender = body.get('gender', '').strip()
    account_type = body.get('account_type', 'teacher' if role == 'teacher' else 'admin').strip()

    if not username or not password or not display_name:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '用户名、密码、显示名不能为空'}, ensure_ascii=False
        )

    password_hash = _hash_password(password)
    db = get_db()

    try:
        with db.cursor() as cursor:
            if account_type == 'admin' or role in ('admin', 'super_admin'):
                if role not in ('admin', 'super_admin'):
                    return 400, [('Content-Type', 'application/json')], json.dumps(
                        {'detail': '管理员角色无效，仅支持 admin 和 super_admin'}, ensure_ascii=False
                    )
                cursor.execute(
                    "INSERT INTO admins (username, password_hash, display_name, role) "
                    "VALUES (%s, %s, %s, %s)",
                    (username, password_hash, display_name, role),
                )
            elif account_type == 'student' or role == 'student':
                cursor.execute(
                    "INSERT INTO students (student_no, name, gender, class_name, major, phone, email, password_hash) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (username, display_name, gender, class_name, major, phone, email, password_hash),
                )
            else:
                cursor.execute(
                    "INSERT INTO teachers (teacher_no, name, phone, email, password_hash) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (username, display_name, phone, email, password_hash),
                )
        db.commit()
    except Exception as e:
        if "Duplicate" in str(e) or "1062" in str(e):
            return 409, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '用户名/工号已存在'}, ensure_ascii=False
            )
        return 500, [('Content-Type', 'application/json')], json.dumps(
            {'detail': str(e)}, ensure_ascii=False
        )

    record_operation_log('user_create', request_handler.headers.get('X-User-Name', request_handler.headers.get('X-User-Role', 'super_admin')), f'{account_type}:{username}')
    return 201, [('Content-Type', 'application/json')], json.dumps(
        {'message': '用户创建成功', 'username': username}, ensure_ascii=False
    )


def handle_update_user(request_handler, user_id):
    """更新用户信息（仅超级管理员）"""
    auth_user = request_handler.headers.get('X-User-Role', '')
    if auth_user != 'super_admin':
        return 403, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无权限，仅超级管理员可操作'}, ensure_ascii=False
        )

    body = request_handler.parse_json_body()
    account_type = body.get('account_type', '').strip() or _infer_account_type(user_id)
    db = get_db()

    if account_type == 'teacher':
        field_map = {
            'username': 'teacher_no',
            'display_name': 'name',
            'phone': 'phone',
            'email': 'email',
            'is_active': 'is_active',
        }
        update_fields = []
        params = []
        for api_field, db_field in field_map.items():
            if api_field in body:
                update_fields.append(f"`{db_field}` = %s")
                params.append(body[api_field])
        if 'password' in body and body['password']:
            update_fields.append("`password_hash` = %s")
            params.append(_hash_password(body['password']))
        if not update_fields:
            return 400, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '没有需要更新的字段'}, ensure_ascii=False
            )
        params.append(user_id)
        with db.cursor() as cursor:
            cursor.execute(
                f"UPDATE teachers SET {', '.join(update_fields)} WHERE id = %s",
                params,
            )
            rowcount = cursor.rowcount
    elif account_type == 'student':
        field_map = {
            'username': 'student_no',
            'display_name': 'name',
            'gender': 'gender',
            'class_name': 'class_name',
            'major': 'major',
            'phone': 'phone',
            'email': 'email',
            'is_active': 'is_active',
        }
        update_fields = []
        params = []
        for api_field, db_field in field_map.items():
            if api_field in body:
                update_fields.append(f"`{db_field}` = %s")
                params.append(body[api_field])
        if 'password' in body and body['password']:
            update_fields.append("`password_hash` = %s")
            params.append(_hash_password(body['password']))
        if not update_fields:
            return 400, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '没有需要更新的字段'}, ensure_ascii=False
            )
        params.append(user_id)
        with db.cursor() as cursor:
            cursor.execute(
                f"UPDATE students SET {', '.join(update_fields)} WHERE id = %s",
                params,
            )
            rowcount = cursor.rowcount
    else:
        update_fields = []
        params = []
        for field in ('username', 'display_name', 'role', 'is_active'):
            if field in body:
                update_fields.append(f"`{field}` = %s")
                params.append(body[field])
        if 'password' in body and body['password']:
            update_fields.append("`password_hash` = %s")
            params.append(_hash_password(body['password']))
        if not update_fields:
            return 400, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '没有需要更新的字段'}, ensure_ascii=False
            )
        params.append(user_id)
        with db.cursor() as cursor:
            cursor.execute(
                f"UPDATE admins SET {', '.join(update_fields)} WHERE id = %s",
                params,
            )
            rowcount = cursor.rowcount

    db.commit()
    if rowcount == 0:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '用户不存在'}, ensure_ascii=False
        )

    record_operation_log('user_update', request_handler.headers.get('X-User-Name', request_handler.headers.get('X-User-Role', 'super_admin')), f'{account_type}:{user_id}')

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'message': '用户更新成功'}, ensure_ascii=False
    )


def handle_delete_user(request_handler, user_id):
    """删除用户（仅超级管理员）"""
    auth_user = request_handler.headers.get('X-User-Role', '')
    if auth_user != 'super_admin':
        return 403, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '无权限，仅超级管理员可操作'}, ensure_ascii=False
        )

    account_type = request_handler.headers.get('X-Account-Type', '').strip() or _infer_account_type(user_id)
    db = get_db()
    with db.cursor() as cursor:
        if account_type == 'teacher':
            cursor.execute("DELETE FROM teachers WHERE id = %s", (user_id,))
        elif account_type == 'student':
            cursor.execute("DELETE FROM students WHERE id = %s", (user_id,))
        else:
            cursor.execute("DELETE FROM admins WHERE id = %s", (user_id,))
        rowcount = cursor.rowcount
    db.commit()

    if rowcount == 0:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '用户不存在'}, ensure_ascii=False
        )

    record_operation_log('user_delete', request_handler.headers.get('X-User-Name', request_handler.headers.get('X-User-Role', 'super_admin')), f'{account_type}:{user_id}')

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'message': '用户删除成功'}, ensure_ascii=False
    )
