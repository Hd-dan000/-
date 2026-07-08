import os
import json
import re
from collections import defaultdict

from database import get_db, dict_from_row, now_str
from config import REPORT_DIR
from services.system_config_service import get_system_config_value, get_system_config_int
from schemas import parse_json_field, serialize_json_field
from services.file_parser import categorize_files

class ReportService:

    def __init__(self, db_conn):
        self.conn = db_conn

    def build_report_data(self, training_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM trainings WHERE id = ?', (training_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('实训项目不存在')
        training = dict_from_row(row)
        cursor.execute('SELECT * FROM submissions WHERE training_id = ? ORDER BY final_score DESC', (training_id,))
        submissions = [dict_from_row(r) for r in cursor.fetchall()]
        cursor.execute('SELECT * FROM evaluation_indicators WHERE training_id = ?', (training_id,))
        indicators = [dict_from_row(r) for r in cursor.fetchall()]
        scores = [s['final_score'] for s in submissions if s['final_score'] is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
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
        evaluated_count = len([s for s in submissions if s['status'] == 'evaluated'])
        pending_count = len([s for s in submissions if s['status'] == 'submitted'])
        ai_evaluated_count = evaluated_count
        pending_manual_review_count = len([s for s in submissions if s['status'] == 'evaluated' and s.get('teacher_score') is None])
        submission_details = []
        for s in submissions:
            eval_detail = parse_json_field(s.get('evaluation_detail'), {})
            files = parse_json_field(s.get('files'), [])
            indicator_summary = eval_detail.get('indicator_summary', [])
            dimension_scores = self._build_dimension_scores(indicator_summary)
            category_scores = self._resolve_category_scores(s, eval_detail)
            categorized = categorize_files(files)
            has_files = bool(files)
            submission_details.append({
                'id': s['id'],
                'student_name': s['student_name'],
                'student_id': s['student_id'],
                'class_id': s.get('class_id'),
                'class_name': s.get('class_name') or '',
                'ai_total_score': s['ai_total_score'],
                'teacher_score': s['teacher_score'],
                'final_score': s['final_score'],
                'status': s['status'],
                'status_label': '已评阅' if s['status'] == 'evaluated' else '未评阅',
                'ai_review_status': '已评阅' if s['status'] == 'evaluated' else '未评阅',
                'document_status': '已提交' if has_files else '未提交',
                'submission_status_label': self._submission_status_label(s['status'], has_files),
                'teacher_comment': s['teacher_comment'],
                'created_at': s['created_at'],
                'indicator_scores': indicator_summary,
                'dimension_scores': dimension_scores,
                'category_scores': category_scores,
                'categories': [cat for cat, items in categorized.items() if items and cat != 'unknown'],
                'overall_comment': eval_detail.get('overall_comment', '')
            })
        return {
            'training': training,
            'statistics': {
                'total_submissions': len(submissions),
                'evaluated_count': evaluated_count,
                'ai_evaluated_count': ai_evaluated_count,
                'pending_manual_review_count': pending_manual_review_count,
                'pending_count': pending_count,
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'score_distribution': distribution
            },
            'indicators': indicators,
            'submissions': submission_details
        }

    def _build_dimension_scores(self, indicator_summary):
        """提取常用维度分数，用于表格列展示；匹配不到时取前3个指标。"""
        default_dims = ['逻辑结构', '代码规范', '功能实现']
        result = {}
        for dim in default_dims:
            found = next((i for i in indicator_summary if dim in i.get('name', '')), None)
            if found:
                result[dim] = found.get('score', 0)
        if not result and indicator_summary:
            for i, item in enumerate(indicator_summary[:3]):
                result[item.get('name', f'维度{i+1}')] = item.get('score', 0)
        for dim in default_dims:
            if dim not in result:
                result[dim] = None
        return result

    def _submission_status_label(self, status, has_files):
        if not has_files:
            return '未提交'
        if status == 'evaluated':
            return '已评阅'
        return '已提交未评阅'

    def _resolve_category_scores(self, submission, eval_detail):
        """合并 AI 分类评分与教师分类评分，教师评分优先。"""
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

    def _get_training_category_weights(self, training_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT category_weights FROM trainings WHERE id = ?', (training_id,))
        row = cursor.fetchone()
        if row and row[0]:
            return parse_json_field(row[0], {'document': 1 / 3, 'ui': 1 / 3, 'code': 1 / 3})
        return {'document': 1 / 3, 'ui': 1 / 3, 'code': 1 / 3}

    def calculate_final_score(self, category_scores, category_weights):
        """按权重计算总分；缺失类别自动归一化剩余权重。"""
        scored = {k: v for k, v in category_scores.items() if v is not None}
        if not scored:
            return None
        total_weight = sum(category_weights.get(k, 0) for k in scored)
        if total_weight == 0:
            return None
        final = sum(scored[k] * category_weights.get(k, 0) for k in scored) / total_weight
        return round(final, 1)

    def get_training_classes(self, training_id):
        """返回实训绑定的班级列表；无精确绑定时回退到已提交班级或课程授课班级。"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT class_id, class_name FROM training_classes WHERE training_id = ? ORDER BY class_name
        ''', (training_id,))
        rows = cursor.fetchall()
        if rows:
            return [{'class_id': r['class_id'], 'class_name': r['class_name'] or f"班级{r['class_id']}"} for r in rows]

        # 回退 1：已存在提交中的班级
        cursor.execute('''
            SELECT DISTINCT class_id, class_name FROM submissions
            WHERE training_id = ? AND class_id IS NOT NULL AND class_id != 0
            ORDER BY class_name
        ''', (training_id,))
        rows = cursor.fetchall()
        if rows:
            return [{'class_id': r['class_id'], 'class_name': r['class_name'] or f"班级{r['class_id']}"} for r in rows]

        # 回退 2：按实训所属课程在 MySQL teach/classes 中查找授课班级
        cursor.execute('SELECT course_id FROM trainings WHERE id = ?', (training_id,))
        trow = cursor.fetchone()
        course_id = trow['course_id'] if trow else None
        if course_id:
            try:
                from database_mysql import get_db as get_mysql_db
                mysql_db = get_mysql_db()
                with mysql_db.cursor() as mc:
                    mc.execute('''
                        SELECT DISTINCT c.id AS class_id, c.class_name
                        FROM teach t
                        JOIN classes c ON c.id = t.class_id
                        WHERE t.course_id = %s AND c.is_active = 1
                        ORDER BY c.class_name
                    ''', (int(course_id),))
                    return [{'class_id': r['class_id'], 'class_name': r['class_name'] or f"班级{r['class_id']}"} for r in mc.fetchall()]
            except Exception:
                pass

        return []

    def list_submissions(self, training_id, class_id=None, student_name=None):
        """按班级/姓名筛选提交记录。"""
        cursor = self.conn.cursor()
        where = ['training_id = ?']
        params = [training_id]
        if class_id:
            where.append('class_id = ?')
            params.append(int(class_id))
        if student_name:
            where.append('(student_name LIKE ? OR student_id LIKE ?)')
            params.extend([f'%{student_name}%', f'%{student_name}%'])
        sql = f"SELECT * FROM submissions WHERE {' AND '.join(where)} ORDER BY created_at DESC"
        cursor.execute(sql, params)
        submissions = [dict_from_row(r) for r in cursor.fetchall()]
        result = []
        for s in submissions:
            eval_detail = parse_json_field(s.get('evaluation_detail'), {})
            files = parse_json_field(s.get('files'), [])
            categorized = categorize_files(files)
            result.append({
                'id': s['id'],
                'student_name': s['student_name'],
                'student_id': s['student_id'],
                'class_id': s.get('class_id'),
                'class_name': s.get('class_name') or '',
                'status': s['status'],
                'submission_status_label': self._submission_status_label(s['status'], bool(files)),
                'ai_total_score': s['ai_total_score'],
                'final_score': s['final_score'],
                'category_scores': self._resolve_category_scores(s, eval_detail),
                'categories': [cat for cat, items in categorized.items() if items and cat != 'unknown'],
                'created_at': s['created_at'],
                'updated_at': s['updated_at']
            })
        return result

    def get_submission_categories(self, submission_id):
        """返回提交文件分类及当前分类评分。"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('提交不存在')
        s = dict_from_row(row)
        eval_detail = parse_json_field(s.get('evaluation_detail'), {})
        files = parse_json_field(s.get('files'), [])
        categorized = categorize_files(files)
        category_ai = eval_detail.get('category_evaluation', {})
        teacher_scores = parse_json_field(s.get('category_teacher_scores'), {})
        teacher_comments = parse_json_field(s.get('category_teacher_comments'), {})
        categories = []
        for cat in ('document', 'ui', 'code'):
            if categorized.get(cat):
                categories.append({
                    'category': cat,
                    'label': {'document': '文档', 'ui': 'UI设计截图', 'code': '源代码'}[cat],
                    'files': categorized[cat],
                    'ai_score': category_ai.get(cat, {}).get('score'),
                    'ai_reason': category_ai.get(cat, {}).get('reason', ''),
                    'teacher_score': teacher_scores.get(cat),
                    'teacher_comment': teacher_comments.get(cat, ''),
                })
        return {
            'submission_id': submission_id,
            'student_name': s['student_name'],
            'student_id': s['student_id'],
            'training_id': s['training_id'],
            'status': s['status'],
            'categories': categories
        }

    def get_category_detail(self, submission_id, categories):
        """返回指定分类的详情，包括文件、AI评价、教师评分。"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('提交不存在')
        s = dict_from_row(row)
        cursor.execute('SELECT * FROM trainings WHERE id = ?', (s['training_id'],))
        training = dict_from_row(cursor.fetchone())
        if training and training.get('category_weights'):
            training['category_weights'] = parse_json_field(training['category_weights'], {'document': 1 / 3, 'ui': 1 / 3, 'code': 1 / 3})
        eval_detail = parse_json_field(s.get('evaluation_detail'), {})
        files = parse_json_field(s.get('files'), [])
        categorized = categorize_files(files)
        category_ai = eval_detail.get('category_evaluation', {})
        teacher_scores = parse_json_field(s.get('category_teacher_scores'), {})
        teacher_comments = parse_json_field(s.get('category_teacher_comments'), {})
        selected = []
        for cat in categories:
            cat_files = categorized.get(cat, [])
            file_details = []
            for f in cat_files:
                path = f.get('path', '')
                relative_url = self._file_path_to_url(path)
                file_details.append({
                    'filename': f.get('filename', ''),
                    'size': f.get('size', 0),
                    'url': relative_url,
                    'is_image': cat == 'ui' or f.get('filename', '').lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'))
                })
            selected.append({
                'category': cat,
                'label': {'document': '文档', 'ui': 'UI设计截图', 'code': '源代码'}[cat],
                'files': file_details,
                'ai_score': category_ai.get(cat, {}).get('score'),
                'ai_reason': category_ai.get(cat, {}).get('reason', ''),
                'teacher_score': teacher_scores.get(cat),
                'teacher_comment': teacher_comments.get(cat, ''),
            })
        return {
            'submission': {
                'id': s['id'],
                'student_name': s['student_name'],
                'student_id': s['student_id'],
                'class_id': s.get('class_id'),
                'class_name': s.get('class_name') or '',
                'status': s['status'],
                'created_at': s['created_at'],
            },
            'training': training,
            'categories': selected,
            'overall_comment': eval_detail.get('overall_comment', ''),
            'teacher_comment': s.get('teacher_comment', '')
        }

    def _file_path_to_url(self, path):
        """将本地绝对/相对路径转换为 /uploads/ 可访问 URL。"""
        if not path:
            return ''
        from config import UPLOAD_DIR
        up = os.path.normpath(path)
        base = os.path.normpath(UPLOAD_DIR)
        if up.startswith(base):
            rel = os.path.relpath(up, base).replace('\\', '/')
            return f'/uploads/{rel}'
        rel = up.replace('\\', '/')
        if rel.startswith('uploads/'):
            return f'/{rel}'
        return f'/uploads/{rel}'

    def save_category_review(self, submission_id, category_scores, category_comments, overall_comment=None):
        """保存教师分类评分，重新计算最终分。"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('提交不存在')
        s = dict_from_row(row)
        training_id = s['training_id']
        category_weights = self._get_training_category_weights(training_id)
        merged_scores = self._resolve_category_scores(s, parse_json_field(s.get('evaluation_detail'), {}))
        for cat, val in category_scores.items():
            if val is not None and val != '':
                try:
                    score = float(val)
                    if 0 <= score <= 100:
                        merged_scores[cat] = score
                except (ValueError, TypeError):
                    pass
        final_score = self.calculate_final_score(merged_scores, category_weights)
        existing_teacher_scores = parse_json_field(s.get('category_teacher_scores'), {})
        existing_teacher_comments = parse_json_field(s.get('category_teacher_comments'), {})
        for cat in ('document', 'ui', 'code'):
            if cat in category_scores:
                existing_teacher_scores[cat] = category_scores[cat]
            if cat in category_comments:
                existing_teacher_comments[cat] = category_comments[cat]
        teacher_comment = s.get('teacher_comment') or ''
        if overall_comment is not None:
            teacher_comment = overall_comment
        cursor.execute('''
            UPDATE submissions
            SET category_teacher_scores = ?, category_teacher_comments = ?, teacher_comment = ?, final_score = ?, status = ?, updated_at = ?
            WHERE id = ?
        ''', (
            json.dumps(existing_teacher_scores, ensure_ascii=False),
            json.dumps(existing_teacher_comments, ensure_ascii=False),
            teacher_comment,
            final_score,
            'evaluated',
            now_str(),
            submission_id
        ))
        self.conn.commit()
        return {'final_score': final_score, 'category_scores': merged_scores}

    def generate_html_report(self, data):
        template = get_system_config_value('report_template', 'standard')
        title_extra = ' - 精简版' if template == 'compact' else ''
        header_color = '#1f6feb' if template == 'standard' else '#16a085'
        card_columns = 'repeat(3, 1fr)' if template == 'standard' else 'repeat(2, 1fr)'
        distribution_values = list(data['statistics']['score_distribution'].values())
        max_distribution = max(distribution_values) if distribution_values else 1
        if max_distribution <= 0:
            max_distribution = 1
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>实训评价报告 - {data['training']['title']}{title_extra}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid {header_color}; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 25px; }}
        .stats-grid {{ display: grid; grid-template-columns: {card_columns}; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: {header_color}; }}
        .stat-card .label {{ color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        tr:hover {{ background: #f8f9fa; }}
        .score-bar {{ height: 20px; background: #eee; border-radius: 10px; overflow: hidden; }}
        .score-fill {{ height: 100%; border-radius: 10px; }}
        .score-excellent {{ background: #28a745; }}
        .score-good {{ background: #17a2b8; }}
        .score-medium {{ background: #ffc107; }}
        .score-pass {{ background: #fd7e14; }}
        .score-fail {{ background: #dc3545; }}
        .comment {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        .chart-container {{ margin: 20px 0; }}
        .bar-chart {{ display: flex; align-items: flex-end; height: 200px; gap: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .bar {{ flex: 1; background: #007bff; border-radius: 5px 5px 0 0; text-align: center; color: white; font-size: 12px; }}
        .bar span {{ display: block; padding-top: 5px; }}
        .footer {{ margin-top: 30px; text-align: center; color: #999; font-size: 12px; }}
        .meta {{ color: #666; font-size: 13px; margin: 8px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 实训评价报告</h1>
        <div class="meta">模板：{('标准模板' if template == 'standard' else '精简模板')}</div>
        <p><strong>实训项目：</strong>{data['training']['title']}</p>
        <p><strong>课程名称：</strong>{data['training']['course_name']}</p>
        <p><strong>指导教师：</strong>{data['training']['teacher_name']}</p>
        <p><strong>生成时间：</strong>{now_str()}</p>
        
        <h2>📊 统计概览</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="value">{data['statistics']['total_submissions']}</div><div class="label">总提交数</div></div>
            <div class="stat-card"><div class="value">{data['statistics']['evaluated_count']}</div><div class="label">已评价数</div></div>
            <div class="stat-card"><div class="value">{data['statistics']['pending_count']}</div><div class="label">待评价数</div></div>
            <div class="stat-card"><div class="value">{data['statistics']['avg_score']}</div><div class="label">平均分</div></div>
            <div class="stat-card"><div class="value">{data['statistics']['max_score']}</div><div class="label">最高分</div></div>
            <div class="stat-card"><div class="value">{data['statistics']['min_score']}</div><div class="label">最低分</div></div>
        </div>
        
        <h2>📈 成绩分布</h2>
        <div class="chart-container">
            <div class="bar-chart">
                {''.join(f'<div class="bar" style="height: {v/max_distribution*100}%"><span>{v}</span></div>' 
                         for v in data['statistics']['score_distribution'].values())}
            </div>
            <div style="display: flex; justify-content: space-around; margin-top: 10px; font-size: 12px; color: #666;">
                {''.join(f'<span>{k}</span>' for k in data['statistics']['score_distribution'].keys())}
            </div>
        </div>
        
        <h2>📝 评价指标</h2>
        <table>
            <tr><th>指标名称</th><th>描述</th><th>权重</th><th>满分</th><th>类型</th></tr>
            {''.join(f'<tr><td>{i["name"]}</td><td>{i["description"]}</td><td>{i["weight"]}</td><td>{i["max_score"]}</td><td>{"自动" if i["indicator_type"]=="auto" else "人工"}</td></tr>' for i in data['indicators'])}
        </table>
        
        <h2>👥 学生成绩详情</h2>
        {''.join(self._render_submission_detail(s) for s in data['submissions'])}
        
        <div class="footer">实训评价系统 - 大模型智能评价</div>
    </div>
</body>
</html>"""
        return html

    def _render_submission_detail(self, s):
        final_score = s['final_score'] if s['final_score'] is not None else 0
        score_class = 'score-excellent' if final_score >= 90 else 'score-good' if final_score >= 80 else 'score-medium' if final_score >= 70 else 'score-pass' if final_score >= 60 else 'score-fail'
        return f"""
        <div style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>学生：</strong>{s['student_name']}
                    {f" (学号: {s['student_id']})" if s['student_id'] else ""}
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 24px; font-weight: bold; color: {'#28a745' if final_score>=60 else '#dc3545'};">{s['final_score'] if s['final_score'] is not None else '-'}</span>
                    <div class="score-bar"><div class="score-fill {score_class}" style="width: {min(final_score, 100)}%"></div></div>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <table style="width: 100%; font-size: 14px;">
                    <tr><th style="width: 20%;">指标</th><th style="width: 10%;">得分</th><th style="width: 10%;">满分</th><th>评价理由</th></tr>
                    {''.join(f'<tr><td>{i["name"]}</td><td>{i["score"]}</td><td>{i["max_score"]}</td><td>{i["reason"]}</td></tr>' for i in s['indicator_scores'])}
                </table>
            </div>
            {f'<div class="comment"><strong>AI评价：</strong>{s["overall_comment"]}</div>' if s['overall_comment'] else ''}
            {f'<div class="comment"><strong>教师评语：</strong>{s["teacher_comment"]}</div>' if s['teacher_comment'] else ''}
        </div>"""

    def generate_csv_report(self, data):
        lines = ['学号,学生姓名,AI评分,教师评分,最终评分,状态']
        for s in data['submissions']:
            lines.append(f"{s['student_id']},{s['student_name']},{s['ai_total_score']},{s['teacher_score']},{s['final_score']},{s['status']}")
        return '\n'.join(lines)

    def save_report(self, training_id, report_type='overall'):
        data = self.build_report_data(training_id)
        html_content = self.generate_html_report(data)
        csv_content = self.generate_csv_report(data)
        timestamp = now_str().replace(':', '-').replace('.', '-')
        report_name = f"{data['training']['title']}_评价报告_{timestamp}"
        html_path = os.path.join(REPORT_DIR, f"{report_name}.html")
        csv_path = os.path.join(REPORT_DIR, f"{report_name}.csv")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO evaluation_reports (training_id, submission_id, report_type, title, content_json, pdf_path, excel_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (training_id, None, report_type, report_name, json.dumps(data, ensure_ascii=False), html_path, csv_path, now_str()))
        self.conn.commit()
        report_id = cursor.lastrowid
        cursor.execute('SELECT * FROM evaluation_reports WHERE id = ?', (report_id,))
        return cursor.fetchone()

    def get_student_detailed_report(self, submission_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('提交不存在')
        submission = dict_from_row(row)
        cursor.execute('SELECT * FROM trainings WHERE id = ?', (submission['training_id'],))
        training = dict_from_row(cursor.fetchone())
        cursor.execute('SELECT * FROM evaluation_indicators WHERE training_id = ?', (submission['training_id'],))
        indicators = [dict_from_row(r) for r in cursor.fetchall()]
        eval_detail = parse_json_field(submission.get('evaluation_detail'), {})
        files = parse_json_field(submission.get('files'), [])
        code_annotations = eval_detail.get('code_annotations', [])
        if not code_annotations and eval_detail.get('ai_scores'):
            code_annotations = self._generate_code_annotations(eval_detail['ai_scores'])
        categorized_files = categorize_files(files)
        return {
            'submission': {
                'id': submission['id'],
                'student_name': submission['student_name'],
                'student_id': submission['student_id'],
                'class_id': submission.get('class_id'),
                'class_name': submission.get('class_name') or '',
                'status': submission['status'],
                'status_label': '已评阅' if submission['status'] == 'evaluated' else '未评阅',
                'document_status': '已提交' if files else '未提交',
                'created_at': submission['created_at'],
                'updated_at': submission['updated_at'],
                'files': files,
                'categorized_files': categorized_files
            },
            'training': training,
            'indicators': indicators,
            'scores': {
                'ai_total_score': submission['ai_total_score'],
                'teacher_score': submission['teacher_score'],
                'final_score': submission['final_score'],
                'indicator_scores': eval_detail.get('indicator_summary', []),
                'ai_scores': eval_detail.get('ai_scores', []),
                'category_scores': self._resolve_category_scores(submission, eval_detail),
                'overall_comment': eval_detail.get('overall_comment', '')
            },
            'teacher_comment': submission.get('teacher_comment', ''),
            'category_teacher_comments': parse_json_field(submission.get('category_teacher_comments'), {}),
            'follow_up_note': submission.get('follow_note', ''),
            'code_annotations': code_annotations,
            'revision_history': self._get_revision_history(submission_id)
        }

    def _generate_code_annotations(self, ai_scores):
        annotations = []
        for score in ai_scores:
            reason = score.get('reason', '')
            if reason and '错误' in reason or '问题' in reason or '建议' in reason:
                annotations.append({
                    'line_number': len(annotations) + 1,
                    'type': 'error' if '错误' in reason else 'warning' if '问题' in reason else 'suggestion',
                    'message': reason,
                    'suggestion': self._extract_suggestion(reason)
                })
        return annotations

    def _extract_suggestion(self, text):
        suggestion_patterns = ['建议', '修改', '改进', '优化']
        for pattern in suggestion_patterns:
            idx = text.find(pattern)
            if idx >= 0:
                return text[idx:].strip()
        return ''

    def _get_revision_history(self, submission_id):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM submission_revisions WHERE submission_id = ? ORDER BY created_at DESC
            ''', (submission_id,))
        except Exception:
            return []
        revisions = []
        for row in cursor.fetchall():
            r = dict_from_row(row)
            r['changes'] = parse_json_field(r.get('changes'), {})
            revisions.append(r)
        return revisions

    def analyze_common_problems(self, training_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE training_id = ? AND status = ?', (training_id, 'evaluated'))
        submissions = [dict_from_row(r) for r in cursor.fetchall()]
        problem_clusters = defaultdict(list)
        for submission in submissions:
            eval_detail = parse_json_field(submission.get('evaluation_detail'), {})
            ai_scores = eval_detail.get('ai_scores', [])
            overall_comment = eval_detail.get('overall_comment', '')
            for score in ai_scores:
                reason = score.get('reason', '')
                if reason and (('错误' in reason) or ('问题' in reason) or ('不足' in reason) or ('缺陷' in reason)):
                    key = self._extract_problem_keyword(reason)
                    if key:
                        problem_clusters[key].append({
                            'submission_id': submission['id'],
                            'student_name': submission['student_name'],
                            'student_id': submission['student_id'],
                            'indicator_name': score['indicator_name'],
                            'score': score['score'],
                            'max_score': score['max_score'],
                            'reason': reason
                        })
            if overall_comment and (('错误' in overall_comment) or ('问题' in overall_comment)):
                key = self._extract_problem_keyword(overall_comment)
                if key:
                    problem_clusters[key].append({
                        'submission_id': submission['id'],
                        'student_name': submission['student_name'],
                        'student_id': submission['student_id'],
                        'indicator_name': '综合评价',
                        'score': submission.get('ai_total_score'),
                        'max_score': 100,
                        'reason': overall_comment
                    })
        sorted_problems = sorted(problem_clusters.items(), key=lambda x: len(x[1]), reverse=True)
        result = []
        for keyword, instances in sorted_problems[:10]:
            student_names = list(set([inst['student_name'] for inst in instances]))
            result.append({
                'keyword': keyword,
                'count': len(instances),
                'student_count': len(student_names),
                'students': student_names,
                'instances': instances[:5],
                'severity': 'high' if len(student_names) >= 5 else 'medium' if len(student_names) >= 2 else 'low'
            })
        return result

    def _extract_problem_keyword(self, text):
        keywords = ['语法错误', '逻辑错误', '缺少', '未实现', '错误', '异常', '漏洞', '缺陷',
                    '不完整', '不正确', '不合理', '格式错误', '命名规范', '注释', '文档']
        for kw in keywords:
            if kw in text:
                return kw
        for pattern in [r'([\u4e00-\u9fa5]{2,4})[错误问题缺陷]', r'([\u4e00-\u9fa5]{2,4})不足']:
            match = re.search(pattern, text)
            if match:
                return match.group(1) + '问题'
        return None

    def get_abnormal_students(self, training_id, threshold=None):
        if threshold is None:
            threshold = get_system_config_int('warning_threshold', 60)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.*, t.title 
            FROM submissions s 
            LEFT JOIN trainings t ON s.training_id = t.id 
            WHERE s.training_id = ? AND s.status = ? AND (s.final_score IS NOT NULL AND s.final_score < ?)
            ORDER BY s.final_score ASC
        ''', (training_id, 'evaluated', threshold))
        submissions = []
        for row in cursor.fetchall():
            s = dict_from_row(row)
            s['files'] = parse_json_field(s.get('files'), [])
            s['evaluation_detail'] = parse_json_field(s.get('evaluation_detail'), {})
            submissions.append(s)
        return submissions

    def generate_single_student_report(self, submission_id):
        data = self.get_student_detailed_report(submission_id)
        html_content = self._generate_single_student_html(data)
        csv_content = self._generate_single_student_csv(data)
        timestamp = now_str().replace(':', '-').replace('.', '-')
        report_name = f"{data['training']['title']}_{data['submission']['student_name']}_评价报告_{timestamp}"
        html_path = os.path.join(REPORT_DIR, f"{report_name}.html")
        csv_path = os.path.join(REPORT_DIR, f"{report_name}.csv")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO evaluation_reports (training_id, submission_id, report_type, title, content_json, pdf_path, excel_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['training']['id'], submission_id, 'single_student', report_name, json.dumps(data, ensure_ascii=False), html_path, csv_path, now_str()))
        self.conn.commit()
        report_id = cursor.lastrowid
        cursor.execute('SELECT * FROM evaluation_reports WHERE id = ?', (report_id,))
        return cursor.fetchone()

    def _generate_single_student_html(self, data):
        s = data['submission']
        sc = data['scores']
        weight_map = {ind['name']: ind.get('weight', 1) for ind in data.get('indicators', [])}
        indicator_rows = ''.join(
            f'<tr><td>{i["name"]}</td><td>{i["score"]}</td><td>{i.get("max_score", 100)}</td><td>{i.get("weight", weight_map.get(i["name"], 1))}</td><td>{i.get("reason", "")}</td></tr>'
            for i in sc['indicator_scores']
        )
        ai_comment = f'<div class="comment-box">{sc["overall_comment"]}</div>' if sc['overall_comment'] else '<div style="color:#999;">暂无AI评语</div>'
        teacher_comment = f'<h2>✏️ 教师评语</h2><div class="comment-box">{data["teacher_comment"]}</div>' if data['teacher_comment'] else ''
        
        annotation_html = ''
        if data['code_annotations']:
            for a in data['code_annotations']:
                suggestion = f"<br><strong>修改建议：</strong>{a['suggestion']}" if a['suggestion'] else ""
                annotation_html += f'<div class="annotation-box annotation-{a["type"]}"><strong>第{a["line_number"]}处</strong>: {a["message"]}{suggestion}</div>'
        else:
            annotation_html = '<div style="color:#999;">暂无代码批注</div>'
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI评阅报告 - {s['student_name']}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; padding: 30px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .info-section {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .info-row {{ display: flex; margin-bottom: 10px; }}
        .info-label {{ width: 120px; font-weight: bold; color: #7f8c8d; }}
        .info-value {{ color: #2c3e50; }}
        .score-card {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .score-item {{ text-align: center; padding: 20px; background: #ecf0f1; border-radius: 8px; }}
        .score-item.final {{ background: #3498db; color: white; }}
        .score-item.final .score-label {{ color: #ecf0f1; }}
        .score-item.final .score-value {{ color: white; }}
        .score-value {{ font-size: 32px; font-weight: bold; color: #3498db; }}
        .score-label {{ font-size: 13px; color: #7f8c8d; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .comment-box {{ background: #e8f4fd; padding: 15px; border-radius: 8px; margin-top: 10px; border-left: 4px solid #3498db; }}
        .annotation-box {{ margin: 15px 0; padding: 15px; border-radius: 8px; }}
        .annotation-error {{ background: #fee2e2; border-left: 4px solid #dc3545; }}
        .annotation-warning {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
        .annotation-suggestion {{ background: #dbeafe; border-left: 4px solid #3b82f6; }}
        .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI智能评阅报告</h1>
        <div class="info-section">
            <div class="info-row"><span class="info-label">学生姓名：</span><span class="info-value">{s['student_name']}</span></div>
            <div class="info-row"><span class="info-label">学号：</span><span class="info-value">{s['student_id'] or '-'}</span></div>
            <div class="info-row"><span class="info-label">实训项目：</span><span class="info-value">{data['training']['title']}</span></div>
            <div class="info-row"><span class="info-label">提交时间：</span><span class="info-value">{s['created_at']}</span></div>
        </div>
        
        <h2>📊 评分概览</h2>
        <div class="score-card">
            <div class="score-item"><div class="score-value">{sc['ai_total_score'] or '-'}</div><div class="score-label">AI评分</div></div>
            <div class="score-item"><div class="score-value">{sc['teacher_score'] or '-'}</div><div class="score-label">教师评分</div></div>
            <div class="score-item"><div class="score-value">{len(s.get('files', []))}</div><div class="score-label">提交文件</div></div>
            <div class="score-item final"><div class="score-value">{sc['final_score'] or '-'}</div><div class="score-label">最终得分</div></div>
        </div>
        
        <h2>📝 各维度评分详情</h2>
        <table>
            <tr><th>评价维度</th><th>得分</th><th>满分</th><th>权重</th><th>评价理由</th></tr>
            {indicator_rows}
        </table>
        
        <h2>💬 AI综合评语</h2>
        {ai_comment}
        
        {teacher_comment}
        
        <h2>🔍 代码批注与修改建议</h2>
        {annotation_html}
        
        <div class="footer">实训评价系统 - AI智能评阅</div>
    </div>
</body>
</html>"""
        return html

    def _generate_single_student_csv(self, data):
        s = data['submission']
        sc = data['scores']
        weight_map = {ind['name']: ind.get('weight', 1) for ind in data.get('indicators', [])}
        lines = [
            f"学生姓名,{s['student_name']}",
            f"学号,{s['student_id'] or ''}",
            f"实训项目,{data['training']['title']}",
            f"提交时间,{s['created_at']}",
            f"AI评分,{sc['ai_total_score'] or ''}",
            f"教师评分,{sc['teacher_score'] or ''}",
            f"最终得分,{sc['final_score'] or ''}",
            f"AI评语,{sc['overall_comment'] or ''}",
            f"教师评语,{data['teacher_comment'] or ''}",
            "",
            "评价维度,得分,满分,权重,评价理由"
        ]
        for i in sc['indicator_scores']:
            lines.append(f"{i['name']},{i['score']},{i.get('max_score', 100)},{i.get('weight', weight_map.get(i['name'], 1))},{i.get('reason', '')}")
        return '\n'.join(lines)

    def generate_batch_reports(self, training_id, format_type='both'):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM submissions WHERE training_id = ? AND status = ?', (training_id, 'evaluated'))
        submission_ids = [r[0] for r in cursor.fetchall()]
        report_ids = []
        for sid in submission_ids:
            try:
                report = self.generate_single_student_report(sid)
                report_ids.append(report['id'])
            except Exception as e:
                print(f"生成报告失败 {sid}: {e}")
        return report_ids