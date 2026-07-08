from database import get_db, dict_from_row


SYSTEM_CONFIG_DEFAULTS = {
    'upload_max_size_mb': '50',
    'report_template': 'standard',
    'enable_submission': '1',
    'enable_evaluation': '1',
    'enable_teacher_review': '1',
    'enable_report_generation': '1',
    'enable_system_maintenance': '0',
}


def get_system_config():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM system_config')
    rows = cursor.fetchall()
    config = {row['key']: row['value'] for row in rows}
    for key, default_value in SYSTEM_CONFIG_DEFAULTS.items():
        if key not in config or config[key] is None or config[key] == '':
            config[key] = default_value
    return config


def get_system_config_value(key, default=None):
    config = get_system_config()
    return config.get(key, default if default is not None else SYSTEM_CONFIG_DEFAULTS.get(key))


def get_system_config_int(key, default=0):
    try:
        return int(get_system_config_value(key, default))
    except (TypeError, ValueError):
        return int(default)


def upsert_system_config(updates):
    conn = get_db()
    cursor = conn.cursor()
    for key, value in updates.items():
        cursor.execute('SELECT key FROM system_config WHERE key = ?', (key,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute('UPDATE system_config SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', (str(value), key))
        else:
            cursor.execute('INSERT INTO system_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)', (key, str(value)))
    conn.commit()
