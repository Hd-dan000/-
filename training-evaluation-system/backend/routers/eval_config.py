import json

from database import get_db, dict_from_row, now_str
from schemas import parse_json_field, serialize_json_field
from routers import auth


def handle_get_eval_config(handler, path):
    training_id = int(path.split('/')[-2])
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM training_evaluation_config WHERE training_id = ?', (training_id,))
    row = cursor.fetchone()

    default_config = {
        'comment_templates': [
            {'min_score': 90, 'max_score': 100, 'label': '优秀', 'template': '该学生表现优秀，代码规范，功能完整，具有较强的创新能力。'},
            {'min_score': 80, 'max_score': 89, 'label': '良好', 'template': '该学生表现良好，代码质量较高，功能实现完整，有一定的创新点。'},
            {'min_score': 70, 'max_score': 79, 'label': '中等', 'template': '该学生基本完成任务，代码规范有待提高，功能实现基本完整。'},
            {'min_score': 60, 'max_score': 69, 'label': '及格', 'template': '该学生勉强完成任务，存在一些问题需要改进。'},
            {'min_score': 0, 'max_score': 59, 'label': '不及格', 'template': '该学生未能完成任务，需要加强学习。'}
        ],
        'error_rules': [
            {'id': 1, 'name': '语法错误', 'keywords': ['SyntaxError', 'IndentationError', 'NameError', 'TypeError'], 'severity': 'high'},
            {'id': 2, 'name': '逻辑漏洞', 'keywords': ['SQL注入', '越界访问', '空指针', '死循环', '内存泄漏'], 'severity': 'high'},
            {'id': 3, 'name': '代码规范', 'keywords': ['未使用变量', '硬编码', '魔数', '过长函数', '嵌套过深'], 'severity': 'medium'},
            {'id': 4, 'name': '性能问题', 'keywords': ['O(n^2)', '重复计算', '内存占用过高', '频繁IO'], 'severity': 'medium'}
        ],
        'alert_thresholds': {
            'min_score': 60,
            'code_completeness': 0.6,
            'low_score_rate': 0.3,
            'suspicious_pattern': True
        },
        'privacy_config': {
            'show_ability_distribution': True,
            'hide_student_name': False,
            'hide_specific_scores': False
        }
    }

    if row:
        data = dict_from_row(row)
        config = {
            'training_id': data['training_id'],
            'comment_templates': parse_json_field(data.get('comment_templates_json'), default_config['comment_templates']),
            'error_rules': parse_json_field(data.get('error_rules_json'), default_config['error_rules']),
            'alert_thresholds': parse_json_field(data.get('alert_thresholds_json'), default_config['alert_thresholds']),
            'privacy_config': parse_json_field(data.get('privacy_config_json'), default_config['privacy_config'])
        }
    else:
        config = {
            'training_id': training_id,
            **default_config
        }

    return 200, [('Content-Type', 'application/json')], json.dumps(config, ensure_ascii=False)


def handle_update_eval_config(handler, path):
    training_id = int(path.split('/')[-2])
    ok, err, _ = auth.check_training_access(handler, training_id)
    if not ok:
        return err

    data = handler.parse_json_body()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM training_evaluation_config WHERE training_id = ?', (training_id,))
    existing = cursor.fetchone()

    comment_templates = data.get('comment_templates', [])
    error_rules = data.get('error_rules', [])
    alert_thresholds = data.get('alert_thresholds', {})
    privacy_config = data.get('privacy_config', {})

    if existing:
        cursor.execute('''
            UPDATE training_evaluation_config
            SET comment_templates_json = ?, error_rules_json = ?,
                alert_thresholds_json = ?, privacy_config_json = ?, updated_at = ?
            WHERE training_id = ?
        ''', (
            serialize_json_field(comment_templates),
            serialize_json_field(error_rules),
            serialize_json_field(alert_thresholds),
            serialize_json_field(privacy_config),
            now_str(),
            training_id
        ))
    else:
        cursor.execute('''
            INSERT INTO training_evaluation_config
            (training_id, comment_templates_json, error_rules_json,
             alert_thresholds_json, privacy_config_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            training_id,
            serialize_json_field(comment_templates),
            serialize_json_field(error_rules),
            serialize_json_field(alert_thresholds),
            serialize_json_field(privacy_config),
            now_str()
        ))

    conn.commit()

    return 200, [('Content-Type', 'application/json')], json.dumps({
        'message': '评价规则配置已保存',
        'training_id': training_id
    }, ensure_ascii=False)