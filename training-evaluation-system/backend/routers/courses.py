# -*- coding: utf-8 -*-
"""课程相关 API
- GET  /api/courses/student/mine  → 学生查看自己的课程列表
- GET  /api/courses/student/<course_id>/trainings  → 学生查看某课程下的实训任务+作业状态
- GET  /api/courses/teacher/mine  → 教师查看自己的授课课程列表
- GET  /api/courses/teacher/<course_id>/classes  → 教师查看某课程下的班级
"""
import json
from datetime import datetime, timedelta
from database_mysql import get_db as get_mysql_db
from database import get_db as get_sqlite_db
from routers import auth


def _first_weekday(year, month, weekday):
    """返回指定年月第一个指定星期几的日期（0=周一）"""
    d = datetime(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def _nth_weekday(year, month, weekday, n):
    """返回指定年月第 n 个指定星期几的日期（n 从 1 开始）"""
    d = _first_weekday(year, month, weekday)
    return d + timedelta(weeks=n - 1)


def _semester_dates(year_start, year_end, term):
    """根据学年跨度与学期编号推导起止日期（基于中国高校常见校历）"""
    term = int(term)
    if term == 1:
        start = _first_weekday(year_start, 9, 0)  # 9 月第一个周一
        end = start + timedelta(weeks=20) - timedelta(days=1)
    elif term == 2:
        start = _nth_weekday(year_end, 2, 0, 3)  # 次年 2 月第 3 个周一
        end = start + timedelta(weeks=20) - timedelta(days=1)
    elif term == 3:
        start = _first_weekday(year_end, 7, 0)  # 次年 7 月第一个周一（短学期）
        end = start + timedelta(weeks=6) - timedelta(days=1)
    else:
        start = datetime(year_start, 9, 1)
        end = start + timedelta(weeks=20) - timedelta(days=1)
    return start, end


def _parse_semester(raw):
    """解析学期字符串，如 2024-2025-1 或 2024-2025-2-3"""
    parts = str(raw).split('-')
    if len(parts) < 3:
        return None
    try:
        year_start = int(parts[0])
        year_end = int(parts[1])
        terms = [int(x) for x in parts[2:]]
        return year_start, year_end, terms
    except ValueError:
        return None


def _group_semesters(semesters):
    groups = {}
    for raw in semesters:
        parsed = _parse_semester(raw)
        if not parsed:
            continue
        year_start, year_end, terms = parsed
        key = f"{year_start}-{year_end}"
        if key not in groups:
            groups[key] = {'year_start': year_start, 'year_end': year_end, 'terms': set()}
        for t in terms:
            groups[key]['terms'].add(t)
    result = []
    for key in sorted(groups.keys(), reverse=True):
        g = groups[key]
        terms = sorted(g['terms'])
        term_text = '、'.join(f"第{t}学期" for t in terms)
        label = f"{key}学年-{term_text}"
        starts = []
        ends = []
        for t in terms:
            s, e = _semester_dates(g['year_start'], g['year_end'], t)
            starts.append(s)
            ends.append(e)
        result.append({
            'value': f"{key}-{terms[0]}",
            'label': label,
            'year_span': key,
            'terms': terms,
            'start_date': min(starts).strftime('%Y-%m-%d'),
            'end_date': max(ends).strftime('%Y-%m-%d'),
        })
    return result


def _find_current_semester(semester_groups):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if not semester_groups:
        return None
    # 优先找包含今天的学期
    for g in semester_groups:
        start = datetime.strptime(g['start_date'], '%Y-%m-%d')
        end = datetime.strptime(g['end_date'], '%Y-%m-%d')
        if start <= today <= end:
            return g, start, end
    # 否则取结束日期最接近今天的学期
    def distance(g):
        end = datetime.strptime(g['end_date'], '%Y-%m-%d')
        return abs((end - today).days)
    g = min(semester_groups, key=distance)
    return g, datetime.strptime(g['start_date'], '%Y-%m-%d'), datetime.strptime(g['end_date'], '%Y-%m-%d')


def handle_student_courses(handler):
    """学生查看自己的课程列表"""
    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_student(user):
        return auth.forbidden('仅学生可访问')

    user_id = user['id']
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute("""
            SELECT c.id, c.course_name, c.course_code, c.semester, c.teacher_name,
                   c.credit, c.description, c.college_id
            FROM student_course sc
            JOIN course c ON c.id = sc.course_id
            WHERE sc.student_id = %s
            ORDER BY c.semester DESC, c.id
        """, (int(user_id),))
        courses = []
        for row in mc.fetchall():
            item = dict(row)
            # 统计该课程下的实训数量（基于该学生的提交）
            mc.execute("""
                SELECT COUNT(*) as cnt FROM submit_work
                WHERE student_id = %s AND course_id = %s
            """, (int(user_id), item['id']))
            cnt_row = mc.fetchone()
            item['submission_count'] = cnt_row['cnt'] if cnt_row else 0
            courses.append(item)

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'total': len(courses), 'courses': courses}, ensure_ascii=False)


def handle_student_all_trainings(handler):
    """学生查看自己已加入课程下的全部实训任务"""
    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_student(user):
        return auth.forbidden('仅学生可访问')

    user_id = user['id']
    mysql_db = get_mysql_db()
    sqlite_db = get_sqlite_db()

    # 查询当前学生姓名与学号
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT student_no, name FROM students WHERE id = %s AND is_active = 1",
            (int(user_id),)
        )
        stu = mc.fetchone()
    if not stu:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '学生信息不存在'}, ensure_ascii=False)

    student_no = stu['student_no']
    student_name = stu['name']

    # 查询学生已加入的课程ID
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT course_id FROM student_course WHERE student_id = %s",
            (int(user_id),)
        )
        course_ids = [row['course_id'] for row in mc.fetchall()]

    if not course_ids:
        return 200, [('Content-Type', 'application/json')], json.dumps(
            {'total': 0, 'trainings': []}, ensure_ascii=False)

    # 查询这些课程下的所有实训
    placeholders = ','.join(['?'] * len(course_ids))
    cursor = sqlite_db.cursor()
    cursor.execute(
        f"SELECT * FROM trainings WHERE course_id IN ({placeholders}) ORDER BY updated_at DESC",
        tuple(course_ids)
    )

    trainings = []
    for row in cursor.fetchall():
        t = dict(row)
        cursor.execute(
            "SELECT id, status, teacher_score, teacher_comment, final_score, created_at FROM submissions "
            "WHERE training_id = ? AND (student_id = ? OR student_name = ?)",
            (t['id'], student_no, student_name)
        )
        sub = cursor.fetchone()
        t['submit_status'] = '已提交' if sub else '未提交'
        if sub:
            t['submission_status'] = sub['status']
            t['teacher_score'] = sub['teacher_score']
            t['teacher_comment'] = sub['teacher_comment']
            t['final_score'] = sub['final_score']
            t['submitted_at'] = sub['created_at']
        trainings.append(t)

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'total': len(trainings), 'trainings': trainings}, ensure_ascii=False)


def handle_student_course_trainings(handler, course_id):
    """学生查看某课程下的实训任务及自己的作业提交状态"""
    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_student(user):
        return auth.forbidden('仅学生可访问')

    user_id = user['id']
    mysql_db = get_mysql_db()
    sqlite_db = get_sqlite_db()

    # 查询当前学生姓名与学号
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT student_no, name FROM students WHERE id = %s AND is_active = 1",
            (int(user_id),)
        )
        stu = mc.fetchone()
    if not stu:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '学生信息不存在'}, ensure_ascii=False)

    student_no = stu['student_no']
    student_name = stu['name']

    if not auth.can_access_course(user, course_id):
        return 403, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '您未加入该课程，无权查看'}, ensure_ascii=False)

    cursor = sqlite_db.cursor()
    cursor.execute("""
        SELECT t.* FROM trainings t
        WHERE t.course_id = ?
        ORDER BY t.created_at DESC
    """, (int(course_id),))
    trainings = []
    for row in cursor.fetchall():
        t = dict(row)
        # 检查该学生是否已提交（按学号或姓名匹配）
        cursor.execute(
            "SELECT id, status, teacher_score, teacher_comment FROM submissions "
            "WHERE training_id = ? AND (student_id = ? OR student_name = ?)",
            (t['id'], student_no, student_name)
        )
        sub = cursor.fetchone()
        t['submit_status'] = '已提交' if sub else '未提交'
        if sub:
            t['submission_status'] = sub['status']
            t['teacher_score'] = sub['teacher_score']
            t['teacher_comment'] = sub['teacher_comment']
        trainings.append(t)

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'course_id': int(course_id), 'total': len(trainings), 'trainings': trainings},
        ensure_ascii=False)


def handle_teacher_courses(handler):
    """教师查看自己的授课课程列表"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    teacher_id = user['id']
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        # 合并 teach 关系与 course.teacher_id 创建的课程
        mc.execute("""
            SELECT DISTINCT c.id, c.course_name, c.course_code, c.semester,
                   c.teacher_name, c.credit, c.college_id
            FROM (
                SELECT course_id AS id FROM teach WHERE teacher_id = %s
                UNION
                SELECT id FROM course WHERE teacher_id = %s
            ) ids
            JOIN course c ON c.id = ids.id
            ORDER BY c.semester DESC, c.id
        """, (int(teacher_id), int(teacher_id)))
        courses = []
        for row in mc.fetchall():
            item = dict(row)
            # 只统计当前教师在该课程下的授课班级数
            mc.execute(
                "SELECT COUNT(*) as cnt FROM teach WHERE course_id = %s AND teacher_id = %s",
                (item['id'], int(teacher_id))
            )
            cnt_row = mc.fetchone()
            item['class_count'] = cnt_row['cnt'] if cnt_row else 0

            # 统计该课程下当前教师所有班级的待批改作业数
            mc.execute(
                "SELECT class_id FROM teach WHERE course_id = %s AND teacher_id = %s",
                (item['id'], int(teacher_id))
            )
            class_ids = [r['class_id'] for r in mc.fetchall()]
            if class_ids:
                ph = ','.join(['%s'] * len(class_ids))
                mc.execute(
                    f"SELECT COUNT(*) as cnt FROM submit_work "
                    f"WHERE course_id = %s AND class_id IN ({ph}) "
                    f"AND (status IS NULL OR status != 'evaluated')",
                    (item['id'], *class_ids)
                )
                pending_row = mc.fetchone()
                item['pending_count'] = pending_row['cnt'] if pending_row else 0
            else:
                item['pending_count'] = 0

            # 封面配色索引
            item['cover_index'] = (item['id'] - 1) % 5
            courses.append(item)

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'total': len(courses), 'courses': courses}, ensure_ascii=False)


def handle_teacher_course_classes(handler, course_id):
    """教师查看某课程下的班级"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    teacher_id = user['id']
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute("""
            SELECT cl.id, cl.class_name, cl.class_code, cl.major, cl.grade, cl.teaching_status,
                   (SELECT COUNT(*) FROM students s WHERE s.class_id = cl.id) as student_count
            FROM teach t
            JOIN classes cl ON cl.id = t.class_id
            WHERE t.course_id = %s AND t.teacher_id = %s
            ORDER BY cl.grade DESC, cl.class_name
        """, (int(course_id), int(teacher_id)))
        classes = [dict(row) for row in mc.fetchall()]
        class_ids = [cls['id'] for cls in classes]

        # 批量查询各班待批改作业数
        pending_map = {}
        if class_ids:
            ph = ','.join(['%s'] * len(class_ids))
            mc.execute(
                f"SELECT class_id, COUNT(*) as cnt FROM submit_work "
                f"WHERE class_id IN ({ph}) AND (status IS NULL OR status != 'evaluated') "
                f"GROUP BY class_id",
                tuple(class_ids)
            )
            for row in mc.fetchall():
                pending_map[row['class_id']] = row['cnt']

        for cls in classes:
            status = cls.get('teaching_status', 'not_started')
            cls['status'] = status
            cls['status_text'] = {
                'not_started': '未开课',
                'in_progress': '开课中',
                'ended': '已结课'
            }.get(status, '未开课')
            cls['pending_count'] = pending_map.get(cls['id'], 0)

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'course_id': int(course_id), 'total': len(classes), 'classes': classes},
        ensure_ascii=False)


def handle_teacher_class_students(handler, class_id):
    """教师查看某班级下的学生及其提交/评价情况"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    teacher_id = int(user['id'])
    class_id = int(class_id)
    mysql_db = get_mysql_db()
    sqlite_db = get_sqlite_db()

    with mysql_db.cursor() as mc:
        # 校验该班级是否属于当前教师
        mc.execute(
            "SELECT 1 FROM teacherclasses WHERE teacher_id = %s AND class_id = %s LIMIT 1",
            (teacher_id, class_id)
        )
        if not mc.fetchone():
            return 403, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '无权操作该班级'}, ensure_ascii=False)

        # 班级信息
        mc.execute(
            "SELECT id, class_code, class_name, major, grade FROM classes "
            "WHERE id = %s AND is_active = 1",
            (class_id,)
        )
        cls = mc.fetchone()
        if not cls:
            return 404, [('Content-Type', 'application/json')], json.dumps(
                {'detail': '班级不存在'}, ensure_ascii=False)

        # 学生列表
        mc.execute(
            "SELECT id, student_no, name, gender, class_name, major FROM students "
            "WHERE class_id = %s AND is_active = 1 ORDER BY student_no",
            (class_id,)
        )
        students = [dict(row) for row in mc.fetchall()]

    # 该班级关联的课程（限制为当前教师授课）
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT course_id FROM teach WHERE class_id = %s AND teacher_id = %s",
            (class_id, teacher_id)
        )
        course_ids = [r['course_id'] for r in mc.fetchall()]

    # 根据课程查 SQLite 实训任务
    training_ids = []
    if course_ids:
        cur = sqlite_db.cursor()
        ph = ','.join(['?'] * len(course_ids))
        cur.execute(
            f"SELECT id FROM trainings WHERE course_id IN ({ph})",
            tuple(course_ids)
        )
        training_ids = [r['id'] for r in cur.fetchall()]

    # MySQL 作业提交记录（按学生 id 聚合）
    hw_map = {}
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT student_id, status, teacher_score FROM submit_work WHERE class_id = %s",
            (class_id,)
        )
        for row in mc.fetchall():
            hw_map.setdefault(row['student_id'], []).append(dict(row))

    # SQLite 大模型评价提交记录（按学号聚合）
    sub_map = {}
    if training_ids:
        cur = sqlite_db.cursor()
        ph = ','.join(['?'] * len(training_ids))
        cur.execute(
            f"SELECT training_id, student_id, student_name, status, "
            f"ai_total_score, final_score FROM submissions "
            f"WHERE training_id IN ({ph})",
            tuple(training_ids)
        )
        for row in cur.fetchall():
            s = dict(row)
            key = s.get('student_id') or s.get('student_name')
            if key:
                sub_map.setdefault(key, []).append(s)

    result = []
    for stu in students:
        key = stu['student_no']
        subs = sub_map.get(key, []) + sub_map.get(stu['name'], [])
        hws = hw_map.get(stu['id'], [])
        evaluated = sum(1 for s in subs if s.get('status') == 'evaluated')

        llm_scores = [s['ai_total_score'] for s in subs if s.get('ai_total_score') is not None]
        final_scores = [s['final_score'] for s in subs if s.get('final_score') is not None]
        teacher_scores = [h['teacher_score'] for h in hws if h.get('teacher_score') is not None]

        result.append({
            **stu,
            'submission_count': len(subs),
            'evaluated_count': evaluated,
            'pending_count': len(subs) - evaluated,
            'llm_score': round(sum(llm_scores) / len(llm_scores), 1) if llm_scores else None,
            'final_score': round(sum(final_scores) / len(final_scores), 1) if final_scores else None,
            'homework_count': len(hws),
            'homework_pending': sum(1 for h in hws if h.get('status') != 'evaluated'),
            'teacher_score': round(sum(teacher_scores) / len(teacher_scores), 1) if teacher_scores else None,
        })

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'class': dict(cls), 'students': result, 'total': len(result)},
        ensure_ascii=False)


def handle_teacher_all_trainings(handler):
    """教师查看自己授课课程下的全部实训任务"""
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    teacher_id = user['id']
    mysql_db = get_mysql_db()
    sqlite_db = get_sqlite_db()

    # 查询教师授课的课程ID及对应班级
    with mysql_db.cursor() as mc:
        mc.execute("""
            SELECT t.course_id, c.class_code, c.class_name
            FROM teach t
            JOIN classes c ON c.id = t.class_id
            WHERE t.teacher_id = %s
            ORDER BY t.course_id, c.class_name
        """, (int(teacher_id),))
        teach_rows = mc.fetchall()

    if not teach_rows:
        return 200, [('Content-Type', 'application/json')], json.dumps(
            {'total': 0, 'trainings': []}, ensure_ascii=False)

    course_classes = {}
    course_ids = set()
    for row in teach_rows:
        cid = row['course_id']
        course_ids.add(cid)
        course_classes.setdefault(cid, []).append(row['class_name'] or row['class_code'])

    # 查询课程名称
    course_names = {}
    if course_ids:
        ph = ','.join(['%s'] * len(course_ids))
        with mysql_db.cursor() as mc:
            mc.execute(f"SELECT id, course_name FROM course WHERE id IN ({ph})", tuple(course_ids))
            for r in mc.fetchall():
                course_names[r['id']] = r['course_name']

    # 查询这些课程下的实训
    placeholders = ','.join(['?'] * len(course_ids))
    cursor = sqlite_db.cursor()
    cursor.execute(
        f"SELECT * FROM trainings WHERE course_id IN ({placeholders}) ORDER BY updated_at DESC",
        tuple(course_ids)
    )

    rows = cursor.fetchall()
    training_ids = [r['id'] for r in rows]

    # 批量查询实训绑定的班级
    training_class_map = {}
    if training_ids:
        ph = ','.join(['?'] * len(training_ids))
        cursor.execute(
            f"SELECT training_id, class_id, class_name FROM training_classes WHERE training_id IN ({ph})",
            tuple(training_ids)
        )
        for r in cursor.fetchall():
            training_class_map.setdefault(r['training_id'], []).append({
                'class_id': r['class_id'],
                'class_name': r['class_name']
            })

    trainings = []
    for row in rows:
        t = dict(row)
        cid = t.get('course_id')

        # 使用 course 表中的课程名称作为项目展示名
        t['courseName'] = course_names.get(cid, '') or t.get('course_name') or t.get('title') or ''

        # 优先使用精确绑定的班级
        bound = training_class_map.get(t['id'], [])
        if bound:
            t['assignedClassIds'] = [b['class_id'] for b in bound]
            t['assignedClasses'] = [b['class_name'] for b in bound if b['class_name']]
            class_ids_for_count = [b['class_id'] for b in bound]
        else:
            t['assignedClassIds'] = []
            t['assignedClasses'] = course_classes.get(cid, [])
            class_ids_for_count = []

        # 统计提交与评价数量
        cursor.execute(
            "SELECT COUNT(*) FROM submissions WHERE training_id = ?",
            (t['id'],)
        )
        t['submissionCount'] = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM submissions WHERE training_id = ? AND status = 'evaluated'",
            (t['id'],)
        )
        t['evaluatedCount'] = cursor.fetchone()[0]
        cursor.execute(
            "SELECT final_score FROM submissions WHERE training_id = ? AND final_score IS NOT NULL",
            (t['id'],)
        )
        scores = [r[0] for r in cursor.fetchall()]
        t['avg_score'] = round(sum(scores) / len(scores), 1) if scores else 0.0

        # 学生总数：优先按绑定班级 ID 统计，无绑定则回退到课程下班级名称
        with mysql_db.cursor() as mc:
            if class_ids_for_count:
                ph2 = ','.join(['%s'] * len(class_ids_for_count))
                mc.execute(
                    f"SELECT COUNT(*) as cnt FROM students WHERE class_id IN ({ph2}) AND is_active = 1",
                    tuple(class_ids_for_count)
                )
                cnt_row = mc.fetchone()
                t['studentCount'] = cnt_row['cnt'] if cnt_row else 0
            else:
                class_names = course_classes.get(cid, [])
                if class_names:
                    placeholders2 = ','.join(['%s'] * len(class_names))
                    mc.execute(
                        f"SELECT COUNT(*) as cnt FROM students WHERE class_name IN ({placeholders2}) AND is_active = 1",
                        tuple(class_names)
                    )
                    cnt_row = mc.fetchone()
                    t['studentCount'] = cnt_row['cnt'] if cnt_row else 0
                else:
                    t['studentCount'] = 0
        trainings.append(t)

    return 200, [('Content-Type', 'application/json')], json.dumps(
        {'total': len(trainings), 'trainings': trainings}, ensure_ascii=False)


def handle_current_semester(handler):
    """工作台：根据 course 表中的学期数据返回当前学期、教学周、剩余天数"""
    user, err = auth.require_user(handler)
    if err:
        return err

    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute("SELECT DISTINCT semester FROM course WHERE semester IS NOT NULL AND semester != ''")
        semesters = [row['semester'] for row in mc.fetchall()]

    groups = _group_semesters(semesters)
    found = _find_current_semester(groups)

    if not found:
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'label': '暂无学期数据',
            'ended': True,
            'week': None,
            'days_remaining': 0
        }, ensure_ascii=False)

    g, start, end = found
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if today > end:
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'label': g['label'],
            'ended': True,
            'week': None,
            'days_remaining': 0,
            'start_date': g['start_date'],
            'end_date': g['end_date']
        }, ensure_ascii=False)

    if today < start:
        days_to_start = (start - today).days
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'label': g['label'],
            'ended': False,
            'week': 0,
            'days_remaining': days_to_start,
            'start_date': g['start_date'],
            'end_date': g['end_date'],
            'not_started': True
        }, ensure_ascii=False)

    week = ((today - start).days // 7) + 1
    days_remaining = (end - today).days
    return 200, [('Content-Type', 'application/json')], json.dumps({
        'label': g['label'],
        'ended': False,
        'week': week,
        'days_remaining': days_remaining,
        'start_date': g['start_date'],
        'end_date': g['end_date']
    }, ensure_ascii=False)
