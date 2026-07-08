import json

from schemas import parse_json_field, serialize_json_field
from database import now_str

class EvaluationEngine:

    def __init__(self, db_conn):
        self.conn = db_conn

    def evaluate_submission(self, submission_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError('提交不存在')
        submission = dict(row)
        cursor.execute('SELECT * FROM trainings WHERE id = ?', (submission['training_id'],))
        training = dict(cursor.fetchone())
        cursor.execute('SELECT * FROM evaluation_indicators WHERE training_id = ?', (submission['training_id'],))
        indicators = [dict(r) for r in cursor.fetchall()]
        parsed_content = submission.get('parsed_content', '')
        if not parsed_content:
            parsed_content = submission.get('files', '')
        auto_indicators = [i for i in indicators if i.get('indicator_type') == 'auto']
        manual_indicators = [i for i in indicators if i.get('indicator_type') == 'manual']
        ai_scores = []
        if auto_indicators:
            try:
                from services.llm_service import llm_service
                llm_result = llm_service.evaluate_content(parsed_content, auto_indicators)
                indicator_scores = llm_result.get('indicator_scores', [])
                for ind in auto_indicators:
                    found = next((s for s in indicator_scores if s.get('indicator_name') == ind['name']), None)
                    if found:
                        score = min(found['score'], ind['max_score'])
                        ai_scores.append({'indicator_id': ind['id'], 'indicator_name': ind['name'],
                                         'score': score, 'max_score': ind['max_score'],
                                         'weight': ind['weight'], 'reason': found.get('reason', '')})
                    else:
                        ai_scores.append({'indicator_id': ind['id'], 'indicator_name': ind['name'],
                                         'score': ind['max_score'] * 0.5, 'max_score': ind['max_score'],
                                         'weight': ind['weight'], 'reason': '未评估'})
                overall_comment = llm_result.get('overall_comment', '')
            except Exception as e:
                for ind in auto_indicators:
                    ai_scores.append({'indicator_id': ind['id'], 'indicator_name': ind['name'],
                                     'score': ind['max_score'] * 0.5, 'max_score': ind['max_score'],
                                     'weight': ind['weight'], 'reason': f'LLM评价失败: {str(e)}'})
                overall_comment = f'LLM评价失败: {str(e)}'
        else:
            for ind in auto_indicators:
                ai_scores.append({'indicator_id': ind['id'], 'indicator_name': ind['name'],
                                 'score': ind['max_score'] * 0.5, 'max_score': ind['max_score'],
                                 'weight': ind['weight'], 'reason': '无自动评价指标'})
            overall_comment = '无自动评价指标'
        total_weight = sum(s['weight'] for s in ai_scores) if ai_scores else 1
        ai_total_score = round(sum(s['score'] * s['weight'] for s in ai_scores) / total_weight, 1) if ai_scores else 0.0
        eval_detail = {
            'ai_scores': ai_scores,
            'overall_comment': overall_comment,
            'indicator_summary': [{'name': s['indicator_name'], 'score': s['score'], 'max_score': s['max_score'], 'reason': s['reason']} for s in ai_scores]
        }
        cursor.execute('UPDATE submissions SET ai_total_score = ?, status = ?, evaluation_detail = ?, updated_at = ? WHERE id = ?',
                      (ai_total_score, 'evaluated', serialize_json_field(eval_detail), now_str(), submission_id))
        self.conn.commit()
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        return cursor.fetchone()

    def batch_evaluate(self, training_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM submissions WHERE training_id = ? AND status = ?', (training_id, 'submitted'))
        submission_ids = [r[0] for r in cursor.fetchall()]
        results = []
        for sid in submission_ids:
            try:
                result = self.evaluate_submission(sid)
                results.append(dict(result))
            except Exception as e:
                print(f"评价失败 {sid}: {e}")
        return results