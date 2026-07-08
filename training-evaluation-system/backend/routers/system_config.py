import json

from schemas import validate_system_config
from services.system_config_service import SYSTEM_CONFIG_DEFAULTS, get_system_config, upsert_system_config
from services.maintenance_service import record_operation_log


def handle_get_system_config():
    config = get_system_config()
    result = {
        'upload': {
            'upload_max_size_mb': int(config.get('upload_max_size_mb', SYSTEM_CONFIG_DEFAULTS['upload_max_size_mb'])),
        },
        'report': {
            'report_template': config.get('report_template', SYSTEM_CONFIG_DEFAULTS['report_template']),
        },
        'switches': {
            'enable_submission': config.get('enable_submission', SYSTEM_CONFIG_DEFAULTS['enable_submission']) == '1',
            'enable_evaluation': config.get('enable_evaluation', SYSTEM_CONFIG_DEFAULTS['enable_evaluation']) == '1',
            'enable_teacher_review': config.get('enable_teacher_review', SYSTEM_CONFIG_DEFAULTS['enable_teacher_review']) == '1',
            'enable_report_generation': config.get('enable_report_generation', SYSTEM_CONFIG_DEFAULTS['enable_report_generation']) == '1',
            'enable_system_maintenance': config.get('enable_system_maintenance', SYSTEM_CONFIG_DEFAULTS['enable_system_maintenance']) == '1',
        },
    }
    return 200, [('Content-Type', 'application/json')], json.dumps(result, ensure_ascii=False)


def handle_update_system_config(handler):
    if handler.headers.get('X-User-Role', '') != 'super_admin':
        return 403, [('Content-Type', 'application/json')], json.dumps({'detail': '无权限，仅超级管理员可操作'}, ensure_ascii=False)

    data = handler.parse_json_body()
    valid, errors = validate_system_config(data)
    if not valid:
        return 400, [('Content-Type', 'application/json')], json.dumps({'detail': errors}, ensure_ascii=False)

    updates = {}
    upload = data.get('upload', {}) or {}
    report = data.get('report', {}) or {}
    switches = data.get('switches', {}) or {}

    if 'upload_max_size_mb' in upload:
        updates['upload_max_size_mb'] = int(upload['upload_max_size_mb'])
    if 'report_template' in report:
        updates['report_template'] = str(report['report_template']).strip()

    for key in ('enable_submission', 'enable_evaluation', 'enable_teacher_review', 'enable_report_generation', 'enable_system_maintenance'):
        if key in switches:
            updates[key] = '1' if bool(switches[key]) else '0'

    upsert_system_config(updates)
    record_operation_log('system_config_update', handler.headers.get('X-User-Name', handler.headers.get('X-User-Role', 'super_admin')), json.dumps(updates, ensure_ascii=False))
    return 200, [('Content-Type', 'application/json')], json.dumps({'message': '系统配置已保存'}, ensure_ascii=False)
