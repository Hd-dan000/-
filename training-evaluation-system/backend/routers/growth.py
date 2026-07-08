# -*- coding: utf-8 -*-
"""学生成长分析聚合接口"""
import json
from collections import defaultdict

from database import get_db as get_sqlite_db, dict_from_row
from database_mysql import get_db as get_mysql_db
from routers import auth
from schemas import parse_json_field


def _safe_avg(values):
    nums = [v for v in values if v is not None]
    return round(sum(nums) / len(nums), 1) if nums else 0.0


def _extract_dimension_scores(eval_detail, category_scores):
    """统一提取四个展示维度：代码规范、逻辑能力、创新度、文档质量。"""
    indicator_summary = (eval_detail or {}).get('indicator_summary', [])
    result = {}

    # 文档质量优先取 category_scores.document
    doc_score = category_scores.get('document')
    if doc_score is not None:
        result['文档质量'] = doc_score
    else:
        found = next((i for i in indicator_summary if '文档' in i.get('name', '')), None)
        if found:
            result['文档质量'] = found.get('score')

    # 代码规范优先取 category_scores.code
    code_score = category_scores.get('code')
    if code_score is not None:
        result['代码规范'] = code_score
    else:
        found = next((i for i in indicator_summary if '代码' in i.get('name', '') or '规范' in i.get('name', '')), None)
        if found:
            result['代码规范'] = found.get('score')

    # 逻辑能力
    found = next((i for i in indicator_summary if '逻辑' in i.get('name', '')), None)
    if found:
        result['逻辑能力'] = found.get('score')

    # 创新度
    found = next((i for i in indicator_summary if '创新' in i.get('name', '')), None)
    if found:
        result['创新度'] = found.get('score')

    return result


def _resolve_category_scores(submission, eval_detail):
    """复用 ReportService 的类别评分归并逻辑。"""
    category_ai = (eval_detail or {}).get('category_evaluation', {})
    teacher_scores = parse_json_field(submission.get('category_teacher_scores'), {})
    result = {}
    for cat in ('document', 'ui', 'code'):
        if teacher_scores.get(cat) is not None:
            result[cat] = float(teacher_scores[cat])
        elif category_ai.get(cat) and category_ai[cat].get('score') is not None:
            result[cat] = float(category_ai[cat]['score'])
        else:
            result[cat] = None
    return result


def _get_class_students(class_id):
    mysql_db = get_mysql_db()
    with mysql_db.cursor() as mc:
        mc.execute(
            "SELECT id, student_no, name, gender FROM students "
            "WHERE class_id = %s AND is_active = 1 ORDER BY student_no",
            (int(class_id),)
        )
        return [dict(row) for row in mc.fetchall()]


def _get_training_course_trainings(training_id):
    """返回与指定实训同课程的所有实训（用于学期成长趋势）。"""
    sqlite_db = get_sqlite_db()
    cursor = sqlite_db.cursor()
    cursor.execute('SELECT course_id FROM trainings WHERE id = ?', (int(training_id),))
    row = cursor.fetchone()
    if not row or not row['course_id']:
        return []
    course_id = row['course_id']
    cursor.execute(
        'SELECT id, title, created_at, updated_at FROM trainings WHERE course_id = ? ORDER BY created_at ASC',
        (int(course_id),)
    )
    return [dict_from_row(r) for r in cursor.fetchall()]


def _get_submissions_for_training_class(training_id, class_id=None):
    """获取某实训下的提交记录，可按班级过滤。"""
    sqlite_db = get_sqlite_db()
    cursor = sqlite_db.cursor()
    where = ['training_id = ?']
    params = [int(training_id)]
    if class_id:
        where.append('class_id = ?')
        params.append(int(class_id))
    cursor.execute(
        f"SELECT * FROM submissions WHERE {' AND '.join(where)} ORDER BY created_at ASC",
        tuple(params)
    )
    return [dict_from_row(r) for r in cursor.fetchall()]


def _build_student_key(student_no, name):
    """学生标识可能来自学号或姓名。"""
    return (student_no or name or '').strip()


def handle_growth_analysis(handler):
    """GET /api/growth/analysis?training_id=X&class_id=Y"""
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)

    training_id = query.get('training_id', [None])[0]
    class_id = query.get('class_id', [None])[0]

    if not training_id:
        return 400, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '缺少training_id参数'}, ensure_ascii=False)

    training_id = int(training_id)
    ok, err, user = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    # 获取实训信息
    sqlite_db = get_sqlite_db()
    cursor = sqlite_db.cursor()
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
    training_row = cursor.fetchone()
    if not training_row:
        return 404, [('Content-Type', 'application/json')], json.dumps(
            {'detail': '实训项目不存在'}, ensure_ascii=False)
    training = dict_from_row(training_row)

    # 班级学生
    class_students = []
    if class_id:
        class_id = int(class_id)
        # 管理员可访问任意班级；教师需校验班级归属
        if not auth.is_admin(user):
            mysql_db = get_mysql_db()
            with mysql_db.cursor() as mc:
                mc.execute(
                    "SELECT 1 FROM teacherclasses WHERE teacher_id = %s AND class_id = %s LIMIT 1",
                    (int(user['id']), class_id)
                )
                if not mc.fetchone():
                    return 403, [('Content-Type', 'application/json')], json.dumps(
                        {'detail': '无权操作该班级'}, ensure_ascii=False)
        class_students = _get_class_students(class_id)

    # 当前实训该班级的提交
    current_submissions = _get_submissions_for_training_class(training_id, class_id)

    # 按学号/姓名建立提交索引
    sub_by_student = {}
    for s in current_submissions:
        key = _build_student_key(s.get('student_id'), s.get('student_name'))
        if key:
            sub_by_student[key] = s

    # 本学期成长趋势：同课程下所有实训的班级平均分走势
    course_trainings = _get_training_course_trainings(training_id)
    trend = []
    if class_id and course_trainings:
        training_ids = [t['id'] for t in course_trainings]
        placeholders = ','.join(['?'] * len(training_ids))
        cursor.execute(
            f"SELECT training_id, final_score, created_at FROM submissions "
            f"WHERE training_id IN ({placeholders}) AND class_id = ? AND status = 'evaluated' AND final_score IS NOT NULL",
            tuple(training_ids + [class_id])
        )
        rows = cursor.fetchall()
        scores_by_training = defaultdict(list)
        for r in rows:
            scores_by_training[r['training_id']].append(r['final_score'])

        for t in course_trainings:
            scores = scores_by_training.get(t['id'], [])
            avg = round(sum(scores) / len(scores), 1) if scores else 0.0
            max_score = max(scores) if scores else 0.0
            trend.append({
                'training_id': t['id'],
                'training_title': t['title'],
                'date': (t['created_at'] or '')[:10],
                'avg_score': avg,
                'max_score': max_score,
                'count': len(scores)
            })
    elif course_trainings:
        # 未选班级时展示整个项目趋势
        training_ids = [t['id'] for t in course_trainings]
        placeholders = ','.join(['?'] * len(training_ids))
        cursor.execute(
            f"SELECT training_id, final_score FROM submissions "
            f"WHERE training_id IN ({placeholders}) AND status = 'evaluated' AND final_score IS NOT NULL",
            tuple(training_ids)
        )
        rows = cursor.fetchall()
        scores_by_training = defaultdict(list)
        for r in rows:
            scores_by_training[r['training_id']].append(r['final_score'])
        for t in course_trainings:
            scores = scores_by_training.get(t['id'], [])
            trend.append({
                'training_id': t['id'],
                'training_title': t['title'],
                'date': (t['created_at'] or '')[:10],
                'avg_score': round(sum(scores) / len(scores), 1) if scores else 0.0,
                'max_score': max(scores) if scores else 0.0,
                'count': len(scores)
            })

    # 能力维度分布：当前实训 + 班级
    dimension_scores = defaultdict(list)
    for s in current_submissions:
        if s['status'] != 'evaluated':
            continue
        eval_detail = parse_json_field(s.get('evaluation_detail'), {})
        category_scores = _resolve_category_scores(s, eval_detail)
        dims = _extract_dimension_scores(eval_detail, category_scores)
        for name, score in dims.items():
            if score is not None:
                dimension_scores[name].append(score)

    dimension_avg = [
        {'name': name, 'value': round(sum(scores) / len(scores), 1)}
        for name, scores in dimension_scores.items()
    ]
    # 补齐四个维度（保证图表顺序）
    all_dims = ['代码规范', '逻辑能力', '创新度', '文档质量']
    dim_map = {d['name']: d['value'] for d in dimension_avg}
    dimension_avg = [{'name': name, 'value': dim_map.get(name, 0.0)} for name in all_dims]

    # 学生列表与标签
    students = []
    if class_students:
        # 历史平均分：用于进步/退步判断（同课程下所有已评价提交）
        course_training_ids = [t['id'] for t in course_trainings]
        history_scores = defaultdict(list)
        if course_training_ids:
            placeholders = ','.join(['?'] * len(course_training_ids))
            cursor.execute(
                f"SELECT student_id, student_name, final_score FROM submissions "
                f"WHERE training_id IN ({placeholders}) AND status = 'evaluated' AND final_score IS NOT NULL",
                tuple(course_training_ids)
            )
            for r in cursor.fetchall():
                for key in (_build_student_key(r['student_id'], r['student_name']), r['student_name']):
                    if key:
                        history_scores[key].append(r['final_score'])

        for stu in class_students:
            key = _build_student_key(stu.get('student_no'), stu.get('name'))
            sub = sub_by_student.get(key)
            is_evaluated = sub and sub.get('status') == 'evaluated'

            current_score = sub.get('final_score') if is_evaluated else None
            eval_detail = parse_json_field(sub.get('evaluation_detail'), {}) if is_evaluated else {}
            category_scores = _resolve_category_scores(sub, eval_detail) if is_evaluated else {}
            dims = _extract_dimension_scores(eval_detail, category_scores)

            history = history_scores.get(key, [])
            historical_avg = round(sum(history) / len(history), 1) if history else None

            # 进步/退步判断
            change = None
            improved = False
            declined = False
            if current_score is not None and historical_avg is not None and len(history) > 1:
                change = round(current_score - historical_avg, 1)
                if change >= 5:
                    improved = True
                elif change <= -5:
                    declined = True

            # 待关注标签
            concern_tags = []
            if current_score is None:
                concern_tags.append('未提交')
            elif current_score < 60:
                concern_tags.append('连续低分')
            elif declined:
                concern_tags.append('提交率下降')
            if dims.get('文档质量') is not None and dims['文档质量'] < 60:
                concern_tags.append('文档薄弱')
            if dims.get('代码规范') is not None and dims['代码规范'] < 60:
                concern_tags.append('代码规范薄弱')
            if dims.get('逻辑能力') is not None and dims['逻辑能力'] < 60:
                concern_tags.append('逻辑能力薄弱')

            # 薄弱/提升维度
            sorted_dims = sorted(dims.items(), key=lambda x: x[1] if x[1] is not None else -1)
            weak_dim = sorted_dims[0][0] if sorted_dims and sorted_dims[0][1] is not None else ''
            strong_dim = sorted_dims[-1][0] if sorted_dims and sorted_dims[-1][1] is not None else ''

            students.append({
                'student_id': stu.get('student_no'),
                'student_name': stu.get('name'),
                'gender': stu.get('gender'),
                'current_score': current_score,
                'historical_avg': historical_avg,
                'change': change,
                'improved': improved,
                'declined': declined,
                'dimension_scores': dims,
                'weak_dimension': weak_dim,
                'strong_dimension': strong_dim,
                'concern_tags': concern_tags,
                'submission_status': sub['status'] if sub else 'not_submitted',
                'submission_id': sub['id'] if sub else None
            })

    # 班级统计
    total_students = len(class_students) if class_students else len(current_submissions)
    submitted_count = len([s for s in current_submissions if s['status'] in ('evaluated', 'submitted')])
    evaluated_count = len([s for s in current_submissions if s['status'] == 'evaluated'])
    final_scores = [s['final_score'] for s in current_submissions if s['final_score'] is not None]
    avg_score = round(sum(final_scores) / len(final_scores), 1) if final_scores else 0.0
    completion_rate = round(evaluated_count / total_students, 2) if total_students else 0.0

    improved_count = sum(1 for s in students if s['improved'])
    concern_count = sum(1 for s in students if s['concern_tags'])

    result = {
        'training': {
            'id': training['id'],
            'title': training['title'],
            'course_id': training.get('course_id'),
            'course_name': training.get('course_name', ''),
        },
        'class_id': class_id,
        'statistics': {
            'student_count': total_students,
            'submitted_count': submitted_count,
            'evaluated_count': evaluated_count,
            'avg_score': avg_score,
            'completion_rate': completion_rate,
            'improved_count': improved_count,
            'concern_count': concern_count
        },
        'trend': trend,
        'dimensions': dimension_avg,
        'students': students
    }

    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)
