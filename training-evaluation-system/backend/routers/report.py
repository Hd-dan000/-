import json
import os
import re
from urllib.parse import quote

from database import get_db, dict_from_row, now_str
from schemas import parse_json_field
from services.report_service import ReportService
from services.system_config_service import get_system_config_value, get_system_config_int
from services.maintenance_service import record_operation_log
from routers import auth


def _content_disposition(filename):
    """生成兼容中文文件名的 Content-Disposition 头"""
    ascii_name = filename.encode('ascii', 'ignore').decode('ascii') or 'download'
    encoded = quote(filename, safe='')
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


def handle_stats(handler):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    conn = get_db()
    cursor = conn.cursor()

    if auth.is_admin(user):
        training_where = ''
        submission_where = ''
        params = []
    else:
        course_ids = auth.get_teacher_course_ids(user['id'])
        if not course_ids:
            return 200, [('Content-Type', 'application/json')], json.dumps({
                'total_trainings': 0, 'total_submissions': 0,
                'evaluated_count': 0, 'avg_score': 0.0,
                'score_distribution': {'优秀(90-100)': 0, '良好(80-89)': 0, '中等(70-79)': 0, '及格(60-69)': 0, '不及格(<60)': 0},
                'recent_submissions': []
            }, ensure_ascii=False)
        placeholders = ','.join(['?'] * len(course_ids))
        training_where = f'WHERE course_id IN ({placeholders})'
        submission_where = f'WHERE training_id IN (SELECT id FROM trainings {training_where})'
        params = list(course_ids)

    def _and(condition):
        return f'AND {condition}' if submission_where else f'WHERE {condition}'

    cursor.execute(f'SELECT COUNT(*) FROM trainings {training_where}', params)
    total_trainings = cursor.fetchone()[0]
    cursor.execute(f'SELECT COUNT(*) FROM submissions {submission_where}', params)
    total_submissions = cursor.fetchone()[0]
    cursor.execute(f"SELECT COUNT(*) FROM submissions {submission_where} {_and('status = ?')}", params + ['evaluated'])
    evaluated_count = cursor.fetchone()[0]
    cursor.execute(f'SELECT final_score FROM submissions {submission_where} {_and("final_score IS NOT NULL")}', params)
    scores = [r[0] for r in cursor.fetchall()]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    distribution = {'优秀(90-100)': 0, '良好(80-89)': 0, '中等(70-79)': 0, '及格(60-69)': 0, '不及格(<60)': 0}
    for s in scores:
        if s >= 90:
            distribution['优秀(90-100)'] += 1
        elif s >= 80:
            distribution['良好(80-89)'] += 1
        elif s >= 70:
            distribution['中等(70-79)'] += 1
        elif s >= 60:
            distribution['及格(60-69)'] += 1
        else:
            distribution['不及格(<60)'] += 1
    cursor.execute(
        f'SELECT s.*, t.title FROM submissions s LEFT JOIN trainings t ON s.training_id = t.id {submission_where} '
        f'ORDER BY s.created_at DESC LIMIT 10',
        params
    )
    recent = cursor.fetchall()
    recent_list = []
    for row in recent:
        s = dict_from_row(row)
        recent_list.append({
            'id': s['id'], 'student_name': s['student_name'],
            'training_title': s.get('title', ''), 'final_score': s['final_score'],
            'status': s['status'], 'created_at': s['created_at']
        })
    result = {
        'total_trainings': total_trainings, 'total_submissions': total_submissions,
        'evaluated_count': evaluated_count, 'avg_score': avg_score,
        'score_distribution': distribution, 'recent_submissions': recent_list
    }
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)

def handle_training_report_data(handler, path):
    training_id = int(re.search(r'/api/report/training/(\d+)/data', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        data = service.build_report_data(training_id)
        return 200, [('Content-Type', 'application/json')], json.dumps(data, ensure_ascii=False)
    except ValueError as e:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_generate_report(handler, path):
    training_id = int(re.search(r'/api/report/generate/(\d+)', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    if get_system_config_int('enable_report_generation', 1) == 0:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '当前系统已关闭报表生成功能'}, ensure_ascii=False)
    try:
        service = ReportService(get_db())
        report = service.save_report(training_id, 'overall')
        r = dict_from_row(report)
        r['content_json'] = parse_json_field(r['content_json'], {})
        record_operation_log('report_generate', 'system', f'training_id={training_id}')
        return 200, [('Content-Type', 'application/json')], json.dumps(r, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_list_reports(handler, path):
    training_id = int(re.search(r'/api/report/list/(\d+)', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_reports WHERE training_id = ? ORDER BY created_at DESC', (training_id,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        r = dict_from_row(row)
        r['content_json'] = parse_json_field(r['content_json'], {})
        result.append(r)
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)

def handle_download_pdf(handler, path):
    report_id = int(re.search(r'/api/report/download/(\d+)/pdf', path).group(1))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT training_id FROM evaluation_reports WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '报告不存在'}, ensure_ascii=False)
    ok, err, _ = auth.check_training_access(handler, row['training_id'])
    if not ok:
        return err
    cursor.execute('SELECT * FROM evaluation_reports WHERE id = ?', (report_id,))
    r = dict_from_row(cursor.fetchone())
    if not r.get('pdf_path') or not os.path.exists(r['pdf_path']):
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': 'PDF文件不存在'}, ensure_ascii=False)
    with open(r['pdf_path'], 'rb') as f:
        content = f.read()
    fname = os.path.basename(r['pdf_path'])
    return 200, [
        ('Content-Type', 'application/pdf'),
        ('Content-Disposition', _content_disposition(fname))
    ], content

def handle_download_excel(handler, path):
    report_id = int(re.search(r'/api/report/download/(\d+)/excel', path).group(1))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT training_id FROM evaluation_reports WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '报告不存在'}, ensure_ascii=False)
    ok, err, _ = auth.check_training_access(handler, row['training_id'])
    if not ok:
        return err
    cursor.execute('SELECT * FROM evaluation_reports WHERE id = ?', (report_id,))
    r = dict_from_row(cursor.fetchone())
    if not r.get('excel_path') or not os.path.exists(r['excel_path']):
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': 'Excel文件不存在'}, ensure_ascii=False)
    with open(r['excel_path'], 'rb') as f:
        content = f.read()
    fname = os.path.basename(r['excel_path'])
    return 200, [
        ('Content-Type', 'text/csv'),
        ('Content-Disposition', _content_disposition(fname))
    ], content

def handle_delete_report(handler, report_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT training_id FROM evaluation_reports WHERE id = ?', (report_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '报告不存在'}, ensure_ascii=False)
    ok, err, _ = auth.check_training_access(handler, row['training_id'])
    if not ok:
        return err
    cursor.execute('SELECT * FROM evaluation_reports WHERE id = ?', (report_id,))
    r = dict_from_row(cursor.fetchone())
    for path in [r.get('pdf_path'), r.get('excel_path')]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    cursor.execute('DELETE FROM evaluation_reports WHERE id = ?', (report_id,))
    conn.commit()
    record_operation_log('report_delete', 'system', f'report_id={report_id}')
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '删除成功'}, ensure_ascii=False)

def handle_student_report(handler, path):
    submission_id = int(re.search(r'/api/report/student/(\d+)', path).group(1))
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        data = service.get_student_detailed_report(submission_id)
        return 200, [('Content-Type', 'application/json')], json.dumps(data, ensure_ascii=False)
    except ValueError as e:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_common_problems(handler, path):
    training_id = int(re.search(r'/api/report/training/(\d+)/common-problems', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        problems = service.analyze_common_problems(training_id)
        return 200, [('Content-Type', 'application/json')], json.dumps(problems, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_abnormal_students(handler, path):
    training_id = int(re.search(r'/api/report/training/(\d+)/abnormal-students', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    params = handler.parse_json_body()
    threshold = params.get('threshold')
    try:
        service = ReportService(get_db())
        students = service.get_abnormal_students(training_id, threshold)
        return 200, [('Content-Type', 'application/json')], json.dumps(students, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_generate_single_student_report(handler, path):
    submission_id = int(re.search(r'/api/report/generate/student/(\d+)', path).group(1))
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        report = service.generate_single_student_report(submission_id)
        r = dict_from_row(report)
        r['content_json'] = parse_json_field(r['content_json'], {})
        return 200, [('Content-Type', 'application/json')], json.dumps(r, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_batch_generate_reports(handler, path):
    training_id = int(re.search(r'/api/report/batch-generate/(\d+)', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        report_ids = service.generate_batch_reports(training_id)
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'message': f'批量生成完成，共生成{len(report_ids)}份报告',
            'report_ids': report_ids
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_export_common_problems(handler, path):
    training_id = int(re.search(r'/api/report/training/(\d+)/export-problems', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        problems = service.analyze_common_problems(training_id)
        from config import REPORT_DIR
        timestamp = now_str().replace(':', '-').replace('.', '-')
        filename = f"共性问题汇总_{timestamp}.csv"
        filepath = os.path.join(REPORT_DIR, filename)
        lines = ['问题关键词,出现次数,涉及学生数,严重程度,涉及学生,典型案例']
        for p in problems:
            students_str = ';'.join(p['students'])
            example = p['instances'][0]['reason'][:100] if p['instances'] else ''
            lines.append(f"{p['keyword']},{p['count']},{p['student_count']},{p['severity']},{students_str},{example}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        with open(filepath, 'rb') as f:
            content = f.read()
        return 200, [
            ('Content-Type', 'text/csv'),
            ('Content-Disposition', _content_disposition(filename))
        ], content
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)

def handle_add_follow_up(handler, path):
    training_id = int(re.search(r'/api/report/training/(\d+)/follow-up', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    params = handler.parse_json_body()
    student_id = params.get('student_id')
    note = params.get('note')
    if not student_id or not note:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '缺少student_id或note参数'}, ensure_ascii=False)
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM submissions WHERE training_id = ? AND student_id = ?', (training_id, student_id))
        row = cursor.fetchone()
        if row:
            cursor.execute('UPDATE submissions SET follow_note = ?, updated_at = ? WHERE id = ?', (note, now_str(), row['id']))
        cursor.execute('INSERT OR REPLACE INTO follow_up_records (student_id, training_id, note, created_at) VALUES (?, ?, ?, ?)',
                       (student_id, training_id, note, now_str()))
        conn.commit()
        return 200, [('Content-Type', 'application/json')], json.dumps({'message': '跟进备注已添加'}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)


def handle_training_classes(handler, path):
    """GET /api/report/classes?training_id={id}"""
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    training_id = query.get('training_id', [None])[0]
    if not training_id:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '缺少training_id'}, ensure_ascii=False)
    ok, err, _ = auth.check_training_access(handler, int(training_id))
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        classes = service.get_training_classes(int(training_id))
        return 200, [('Content-Type', 'application/json')], json.dumps({'classes': classes}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)


def handle_list_submissions(handler, path):
    """GET /api/report/submissions?training_id={id}&class_id={cid}&student_name={name}"""
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    training_id = query.get('training_id', [None])[0]
    class_id = query.get('class_id', [None])[0]
    student_name = query.get('student_name', [None])[0]
    if not training_id:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '缺少training_id'}, ensure_ascii=False)
    ok, err, _ = auth.check_training_access(handler, int(training_id))
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        submissions = service.list_submissions(
            int(training_id),
            class_id=int(class_id) if class_id else None,
            student_name=student_name.strip() if student_name else None
        )
        return 200, [('Content-Type', 'application/json')], json.dumps({'total': len(submissions), 'submissions': submissions}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)


def handle_submission_categories(handler, path):
    """GET /api/report/submission/{id}/categories"""
    submission_id = int(re.search(r'/api/report/submission/(\d+)/categories', path).group(1))
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    try:
        service = ReportService(get_db())
        data = service.get_submission_categories(submission_id)
        return 200, [('Content-Type', 'application/json')], json.dumps(data, ensure_ascii=False)
    except ValueError as e:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)


def handle_category_detail(handler, path):
    """GET /api/report/submission/{id}/detail?categories=document,ui,code"""
    submission_id = int(re.search(r'/api/report/submission/(\d+)/detail', path).group(1))
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    categories_param = query.get('categories', [''])[0]
    categories = [c.strip() for c in categories_param.split(',') if c.strip() in ('document', 'ui', 'code')]
    if not categories:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '缺少有效的categories参数'}, ensure_ascii=False)
    try:
        service = ReportService(get_db())
        data = service.get_category_detail(submission_id, categories)
        return 200, [('Content-Type', 'application/json')], json.dumps(data, ensure_ascii=False)
    except ValueError as e:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)


def handle_category_review(handler, path):
    """POST /api/report/submission/{id}/category-review"""
    submission_id = int(re.search(r'/api/report/submission/(\d+)/category-review', path).group(1))
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    params = handler.parse_json_body()
    category_scores = params.get('category_scores', {})
    category_comments = params.get('category_comments', {})
    overall_comment = params.get('overall_comment')
    try:
        service = ReportService(get_db())
        result = service.save_category_review(submission_id, category_scores, category_comments, overall_comment)
        record_operation_log('category_review', handler.headers.get('X-User-Name', 'teacher'), f'submission_id={submission_id}')
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'message': '分类评分已保存',
            'final_score': result['final_score'],
            'category_scores': result['category_scores']
        }, ensure_ascii=False)
    except ValueError as e:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)