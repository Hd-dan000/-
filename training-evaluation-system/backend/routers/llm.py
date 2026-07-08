import json

from database import get_db, dict_from_row, now_str
from schemas import validate_llm_config
from services.llm_service import llm_service
from routers import auth

def handle_get_llm_config(handler):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM system_config')
    rows = cursor.fetchall()
    config = {}
    for row in rows:
        config[row['key']] = row['value']
    defaults = {
        'provider': llm_service.provider,
        'api_base': llm_service.api_base,
        'model': llm_service.model,
        'ollama_host': llm_service.ollama_host,
        'ollama_model': llm_service.ollama_model,
    }
    for k, v in defaults.items():
        if k not in config:
            config[k] = v
    if 'api_key' in config:
        config['api_key'] = config['api_key'][:8] + '****' if config['api_key'] else ''
    return 200, [('Content-Type', 'application/json')], json.dumps(config, ensure_ascii=False)

def handle_update_llm_config(handler):
    user, err = auth.require_user(handler)
    if err:
        return err
    if not auth.is_admin(user):
        return auth.forbidden('仅管理员可更新大模型配置')

    data = handler.parse_json_body()
    valid, errors = validate_llm_config(data)
    if not valid:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': errors}, ensure_ascii=False)
    conn = get_db()
    cursor = conn.cursor()
    updates = {}
    for key, value in data.items():
        if value is not None:
            updates[key] = value
            cursor.execute('SELECT * FROM system_config WHERE key = ?', (key,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute('UPDATE system_config SET value = ?, updated_at = ? WHERE key = ?',
                              (str(value), now_str(), key))
            else:
                cursor.execute('INSERT INTO system_config (key, value, updated_at) VALUES (?, ?, ?)',
                              (key, str(value), now_str()))
    conn.commit()
    llm_service.update_config(**updates)
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '配置更新成功'}, ensure_ascii=False)

def handle_test_llm_connection(handler):
    user, err = auth.require_teacher_or_admin(handler)
    if err:
        return err

    data = handler.parse_json_body()
    prompt = data.get('prompt', '你好，请简要介绍你自己。')
    try:
        success, response, latency = llm_service.test_connection(prompt)
        result = {'success': success, 'response': response, 'latency_ms': round(latency, 0)}
        return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return 500, [('Content-Type', 'application/json')], json.dumps({'detail': str(e)}, ensure_ascii=False)