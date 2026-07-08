import json
import re

from database import get_db, dict_from_row, now_str
from schemas import validate_indicator_create, parse_json_field, serialize_json_field
from services.evaluation_service import EvaluationEngine
from services.system_config_service import get_system_config_int
from services.maintenance_service import record_operation_log
from routers import auth


def _get_user_info(handler):
    return {
        'name': handler.headers.get('X-User-Name', ''),
        'role': handler.headers.get('X-User-Role', 'teacher'),
        'display_name': handler.headers.get('X-User-Display-Name', '')
    }


def _serialize_template(row):
    data = dict_from_row(row)
    data['indicators'] = parse_json_field(data.get('indicators_json'), [])
    data['indicator_count'] = len(data['indicators']) if isinstance(data['indicators'], list) else 0
    data['comment_templates'] = parse_json_field(data.get('comment_templates_json'), [])
    data['error_rules'] = parse_json_field(data.get('error_rules_json'), [])
    data['alert_thresholds'] = parse_json_field(data.get('alert_thresholds_json'), {})
    data['privacy_config'] = parse_json_field(data.get('privacy_config_json'), {})
    return data


def handle_list_templates(handler):
    user = _get_user_info(handler)
    conn = get_db()
    cursor = conn.cursor()
    if user['role'] == 'super_admin':
        cursor.execute('SELECT * FROM evaluation_templates ORDER BY is_default DESC, created_at DESC')
    else:
        cursor.execute('''
            SELECT * FROM evaluation_templates 
            WHERE created_by = ? OR is_default = 1 
            ORDER BY is_default DESC, created_at DESC
        ''', (user['name'],))
    rows = cursor.fetchall()
    return 200, [('Content-Type', 'application/json')], json.dumps([_serialize_template(r) for r in rows], ensure_ascii=False)


def handle_get_template(handler, template_id):
    user = _get_user_info(handler)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    if not template:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '模板不存在'}, ensure_ascii=False)
    
    template_data = dict_from_row(template)
    if user['role'] != 'super_admin' and template_data.get('created_by') != user['name'] and not template_data.get('is_default'):
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权查看该模板'}, ensure_ascii=False)
    
    return 200, [('Content-Type', 'application/json')], json.dumps(_serialize_template(template), ensure_ascii=False)


def handle_create_template(handler):
    user = _get_user_info(handler)
    if user['role'] not in ['super_admin', 'teacher']:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权限，仅教师和管理员可创建模板'}, ensure_ascii=False)
    
    data = handler.parse_json_body()
    name = (data.get('name') or '').strip()
    if not name:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '模板名称不能为空'}, ensure_ascii=False)
    
    indicators = data.get('indicators', [])
    if isinstance(indicators, str):
        indicators = parse_json_field(indicators, [])
    if not isinstance(indicators, list):
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': 'indicators 必须是数组'}, ensure_ascii=False)
    
    comment_templates = data.get('comment_templates', [])
    error_rules = data.get('error_rules', [])
    alert_thresholds = data.get('alert_thresholds', {})
    privacy_config = data.get('privacy_config', {})
    
    conn = get_db()
    cursor = conn.cursor()
    
    is_default = 1 if data.get('is_default') else 0
    if is_default and user['role'] != 'super_admin':
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '仅超级管理员可设为默认模板'}, ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO evaluation_templates 
        (name, description, indicators_json, comment_templates_json, error_rules_json, 
         alert_thresholds_json, privacy_config_json, is_default, created_by, created_by_role, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        name, data.get('description', ''), serialize_json_field(indicators),
        serialize_json_field(comment_templates), serialize_json_field(error_rules),
        serialize_json_field(alert_thresholds), serialize_json_field(privacy_config),
        is_default, user['name'], user['role'], now_str(), now_str()
    ))
    template_id = cursor.lastrowid
    
    if is_default:
        cursor.execute('UPDATE evaluation_templates SET is_default = 0 WHERE id != ?', (template_id,))
    
    conn.commit()
    record_operation_log('template_create', user['name'], name)
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    return 200, [('Content-Type', 'application/json')], json.dumps(_serialize_template(cursor.fetchone()), ensure_ascii=False)


def handle_update_template(handler, template_id):
    user = _get_user_info(handler)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    if not template:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '模板不存在'}, ensure_ascii=False)
    
    template_data = dict_from_row(template)
    if user['role'] != 'super_admin' and template_data.get('created_by') != user['name']:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权修改他人模板'}, ensure_ascii=False)
    
    data = handler.parse_json_body()
    fields = []
    values = []
    
    for key in ['name', 'description']:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    
    if 'indicators' in data:
        indicators = data['indicators']
        if isinstance(indicators, str):
            indicators = parse_json_field(indicators, [])
        if not isinstance(indicators, list):
            return 400, [('Content-Type', 'application/json')], json.dumps({'detail': 'indicators 必须是数组'}, ensure_ascii=False)
        fields.append('indicators_json = ?')
        values.append(serialize_json_field(indicators))
    
    if 'comment_templates' in data:
        fields.append('comment_templates_json = ?')
        values.append(serialize_json_field(data['comment_templates']))
    
    if 'error_rules' in data:
        fields.append('error_rules_json = ?')
        values.append(serialize_json_field(data['error_rules']))
    
    if 'alert_thresholds' in data:
        fields.append('alert_thresholds_json = ?')
        values.append(serialize_json_field(data['alert_thresholds']))
    
    if 'privacy_config' in data:
        fields.append('privacy_config_json = ?')
        values.append(serialize_json_field(data['privacy_config']))
    
    if 'is_default' in data:
        if data['is_default'] and user['role'] != 'super_admin':
            return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '仅超级管理员可设为默认模板'}, ensure_ascii=False)
        fields.append('is_default = ?')
        values.append(1 if data['is_default'] else 0)
    
    if not fields:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '没有需要更新的字段'}, ensure_ascii=False)
    
    fields.append('updated_at = ?')
    values.append(now_str())
    values.append(template_id)
    
    cursor.execute(f'UPDATE evaluation_templates SET {", ".join(fields)} WHERE id = ?', values)
    
    if data.get('is_default'):
        cursor.execute('UPDATE evaluation_templates SET is_default = 0 WHERE id != ?', (template_id,))
    
    conn.commit()
    record_operation_log('template_update', user['name'], f'id={template_id}')
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    return 200, [('Content-Type', 'application/json')], json.dumps(_serialize_template(cursor.fetchone()), ensure_ascii=False)


def handle_delete_template(handler, template_id):
    user = _get_user_info(handler)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    if not template:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '模板不存在'}, ensure_ascii=False)
    
    template_data = dict_from_row(template)
    if user['role'] != 'super_admin' and template_data.get('created_by') != user['name']:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权删除他人模板'}, ensure_ascii=False)
    
    cursor.execute('DELETE FROM evaluation_templates WHERE id = ?', (template_id,))
    conn.commit()
    record_operation_log('template_delete', user['name'], f'id={template_id}')
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '删除成功'}, ensure_ascii=False)


def handle_assign_template(handler, template_id):
    user = _get_user_info(handler)
    if user['role'] not in ['super_admin', 'teacher']:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权限分配模板'}, ensure_ascii=False)
    
    data = handler.parse_json_body()
    training_ids = data.get('training_ids', [])
    if not isinstance(training_ids, list) or len(training_ids) == 0:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': 'training_ids 必须是非空数组'}, ensure_ascii=False)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    if not template:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '模板不存在'}, ensure_ascii=False)
    
    template_data = _serialize_template(template)
    
    assigned_count = 0
    for training_id in training_ids:
        try:
            if user['role'] != 'super_admin':
                cursor.execute('SELECT course_id FROM trainings WHERE id = ?', (training_id,))
                row = cursor.fetchone()
                if not row:
                    continue
            
            cursor.execute('SELECT * FROM training_template_assignments WHERE training_id = ? AND template_id = ?', (training_id, template_id))
            if cursor.fetchone():
                cursor.execute('UPDATE training_template_assignments SET assigned_by = ?, assigned_at = ? WHERE training_id = ? AND template_id = ?',
                             (user['name'], now_str(), training_id, template_id))
            else:
                cursor.execute('INSERT INTO training_template_assignments (training_id, template_id, assigned_by, assigned_at) VALUES (?, ?, ?, ?)',
                             (training_id, template_id, user['name'], now_str()))
            
            cursor.execute('DELETE FROM evaluation_indicators WHERE training_id = ?', (training_id,))
            for indicator in template_data['indicators']:
                cursor.execute('''
                    INSERT INTO evaluation_indicators (training_id, name, description, weight, max_score, indicator_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (training_id, indicator.get('name', ''), indicator.get('description', ''),
                      indicator.get('weight', 1.0), indicator.get('max_score', 100.0), indicator.get('indicator_type', 'auto'), now_str()))
            
            cursor.execute('SELECT * FROM training_evaluation_config WHERE training_id = ?', (training_id,))
            if cursor.fetchone():
                cursor.execute('''
                    UPDATE training_evaluation_config 
                    SET comment_templates_json = ?, error_rules_json = ?, alert_thresholds_json = ?, privacy_config_json = ?, updated_at = ?
                    WHERE training_id = ?
                ''', (
                    serialize_json_field(template_data['comment_templates']),
                    serialize_json_field(template_data['error_rules']),
                    serialize_json_field(template_data['alert_thresholds']),
                    serialize_json_field(template_data['privacy_config']),
                    now_str(), training_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO training_evaluation_config 
                    (training_id, comment_templates_json, error_rules_json, alert_thresholds_json, privacy_config_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    training_id,
                    serialize_json_field(template_data['comment_templates']),
                    serialize_json_field(template_data['error_rules']),
                    serialize_json_field(template_data['alert_thresholds']),
                    serialize_json_field(template_data['privacy_config']),
                    now_str()
                ))
            
            assigned_count += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"分配模板到实训 {training_id} 失败: {e}")
    
    conn.commit()
    record_operation_log('template_assign', user['name'], f'template_id={template_id}, trainings={training_ids}')
    
    return 200, [('Content-Type', 'application/json')], json.dumps({
        'message': f'模板分配完成，成功分配 {assigned_count} 个实训项目',
        'assigned_count': assigned_count,
        'total_requested': len(training_ids)
    }, ensure_ascii=False)


def handle_get_template_assignments(handler, template_id):
    user = _get_user_info(handler)
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM evaluation_templates WHERE id = ?', (template_id,))
    template = cursor.fetchone()
    if not template:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '模板不存在'}, ensure_ascii=False)
    
    template_data = dict_from_row(template)
    if user['role'] != 'super_admin' and template_data.get('created_by') != user['name']:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权查看他人模板的分配情况'}, ensure_ascii=False)
    
    cursor.execute('''
        SELECT ta.*, t.title, t.course_name, t.status 
        FROM training_template_assignments ta
        JOIN trainings t ON ta.training_id = t.id
        WHERE ta.template_id = ?
        ORDER BY ta.assigned_at DESC
    ''', (template_id,))
    rows = cursor.fetchall()
    
    return 200, [('Content-Type', 'application/json')], json.dumps([dict_from_row(r) for r in rows], ensure_ascii=False)

def handle_list_indicators(handler, path):
    training_id = int(re.search(r'/api/evaluation/indicators/(\d+)', path).group(1))
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_indicators WHERE training_id = ?', (training_id,))
    rows = cursor.fetchall()
    return 200, [('Content-Type', 'application/json')], json.dumps([dict_from_row(r) for r in rows], ensure_ascii=False)

def handle_create_indicator(handler):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    data = handler.parse_json_body()
    valid, errors = validate_indicator_create(data)
    if not valid:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': errors}, ensure_ascii=False)

    training_id = data.get('training_id')
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evaluation_indicators (training_id, name, description, weight, max_score, indicator_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (training_id, data.get('name'), data.get('description'),
          data.get('weight', 1.0), data.get('max_score', 100.0), data.get('indicator_type', 'auto'), now_str()))
    conn.commit()
    indicator_id = cursor.lastrowid
    cursor.execute('SELECT * FROM evaluation_indicators WHERE id = ?', (indicator_id,))
    return 200, [('Content-Type', 'application/json')], json.dumps(dict_from_row(cursor.fetchone()), ensure_ascii=False)

def handle_update_indicator(handler, indicator_id):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    ok, err, _ = auth.check_indicator_access(handler, indicator_id)
    if not ok:
        return err

    data = handler.parse_json_body()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_indicators WHERE id = ?', (indicator_id,))
    if not cursor.fetchone():
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '指标不存在'}, ensure_ascii=False)
    fields = []
    values = []
    for k in ['name', 'description', 'weight', 'max_score', 'indicator_type']:
        if k in data:
            fields.append(f"{k} = ?")
            values.append(data[k])
    values.append(indicator_id)
    cursor.execute(f'UPDATE evaluation_indicators SET {", ".join(fields)} WHERE id = ?', values)
    conn.commit()
    cursor.execute('SELECT * FROM evaluation_indicators WHERE id = ?', (indicator_id,))
    return 200, [('Content-Type', 'application/json')], json.dumps(dict_from_row(cursor.fetchone()), ensure_ascii=False)

def handle_delete_indicator(handler, indicator_id):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    ok, err, _ = auth.check_indicator_access(handler, indicator_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evaluation_indicators WHERE id = ?', (indicator_id,))
    if not cursor.fetchone():
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '指标不存在'}, ensure_ascii=False)
    cursor.execute('DELETE FROM evaluation_indicators WHERE id = ?', (indicator_id,))
    conn.commit()
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '删除成功'}, ensure_ascii=False)

def handle_evaluate_submission(handler, path):
    submission_id = int(re.search(r'/api/evaluation/evaluate/(\d+)', path).group(1))
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    if get_system_config_int('enable_evaluation', 1) == 0:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '当前系统已关闭自动评价功能'}, ensure_ascii=False)
    try:
        engine = EvaluationEngine(get_db())
        result = engine.evaluate_submission(submission_id)
        s = dict_from_row(result)
        s['files'] = parse_json_field(s['files'], [])
        s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
        return 200, [('Content-Type', 'application/json')], json.dumps(s, ensure_ascii=False)
    except ValueError as e:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': f'评价失败: {str(e)}'}, ensure_ascii=False)

def handle_batch_evaluate(handler, path):
    training_id = int(re.search(r'/api/evaluation/batch-evaluate/(\d+)', path).group(1))
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err
    if get_system_config_int('enable_evaluation', 1) == 0:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '当前系统已关闭自动评价功能'}, ensure_ascii=False)
    try:
        engine = EvaluationEngine(get_db())
        results = engine.batch_evaluate(training_id)
        return 200, [('Content-Type', 'application/json')], json.dumps({
            'message': f'评价完成，共处理{len(results)}个提交',
            'evaluated_count': len(results)
        }, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': f'批量评价失败: {str(e)}'}, ensure_ascii=False)

def handle_teacher_review(handler, path):
    submission_id = int(re.search(r'/api/evaluation/teacher-review/(\d+)', path).group(1))
    if get_system_config_int('enable_teacher_review', 1) == 0:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '当前系统已关闭教师补评功能'}, ensure_ascii=False)
    data = handler.parse_json_body()

    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '提交不存在'}, ensure_ascii=False)
    submission = dict_from_row(row)
    if 'teacher_score' in data and data['teacher_score'] is not None:
        cursor.execute('UPDATE submissions SET teacher_score = ?, updated_at = ? WHERE id = ?',
                      (data['teacher_score'], now_str(), submission_id))
    if 'teacher_comment' in data and data['teacher_comment'] is not None:
        cursor.execute('UPDATE submissions SET teacher_comment = ?, updated_at = ? WHERE id = ?',
                      (data['teacher_comment'], now_str(), submission_id))
    cursor.execute('SELECT * FROM evaluation_indicators WHERE training_id = ?', (submission['training_id'],))
    indicators = cursor.fetchall()
    if submission.get('ai_total_score') is not None and data.get('teacher_score') is not None:
        if indicators:
            auto_weight = sum(i['weight'] for i in [dict_from_row(x) for x in indicators] if i['indicator_type'] == 'auto')
            manual_weight = sum(i['weight'] for i in [dict_from_row(x) for x in indicators] if i['indicator_type'] == 'manual')
            total_w = auto_weight + manual_weight
            if total_w > 0:
                final_score = round(submission['ai_total_score'] * auto_weight / total_w + data['teacher_score'] * manual_weight / total_w, 1)
            else:
                final_score = submission['ai_total_score']
        else:
            final_score = round(submission['ai_total_score'] * 0.6 + data['teacher_score'] * 0.4, 1)
        cursor.execute('UPDATE submissions SET final_score = ?, updated_at = ? WHERE id = ?',
                      (final_score, now_str(), submission_id))
    conn.commit()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    s = dict_from_row(cursor.fetchone())
    s['files'] = parse_json_field(s['files'], [])
    s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
    return 200, [('Content-Type', 'application/json')], json.dumps(s, ensure_ascii=False)

def handle_reparse_submission(handler, path):
    submission_id = int(re.search(r'/api/evaluation/reparse/(\d+)', path).group(1))
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err
    ok, err, _ = auth.check_submission_access(handler, submission_id)
    if not ok:
        return err
    if get_system_config_int('enable_evaluation', 1) == 0:
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '当前系统已关闭自动评价功能'}, ensure_ascii=False)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    row = cursor.fetchone()
    if not row:
        return 404, [('Content-Type', 'application/json')], json.dumps({'detail': '提交不存在'}, ensure_ascii=False)
    submission = dict_from_row(row)
    files = parse_json_field(submission['files'], [])
    if not files:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': '没有上传文件'}, ensure_ascii=False)
    cursor.execute('SELECT * FROM trainings WHERE id = ?', (submission['training_id'],))
    training = dict_from_row(cursor.fetchone())
    from services.file_parser import parse_files_to_text
    filepaths = [f['path'] for f in files]
    parsed = parse_files_to_text(filepaths)
    try:
        from services.llm_service import llm_service
        llm_result = llm_service.parse_submission(
            parsed, training.get('expected_steps', ''), training.get('expected_outcomes', '')
        )
        parsed_content = llm_result.get('summary', str(llm_result))
        eval_detail = parse_json_field(submission.get('evaluation_detail'), {})
        eval_detail['llm_parse'] = llm_result
        cursor.execute('UPDATE submissions SET parsed_content = ?, evaluation_detail = ?, updated_at = ? WHERE id = ?',
                      (parsed_content, serialize_json_field(eval_detail), now_str(), submission_id))
        conn.commit()
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': f'大模型解析失败: {str(e)}'}, ensure_ascii=False)
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    s = dict_from_row(cursor.fetchone())
    s['files'] = parse_json_field(s['files'], [])
    s['evaluation_detail'] = parse_json_field(s['evaluation_detail'], {})
    return 200, [('Content-Type', 'application/json')], json.dumps(s, ensure_ascii=False)