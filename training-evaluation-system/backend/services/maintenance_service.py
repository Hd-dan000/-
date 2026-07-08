import json
import os
import shutil
import sqlite3
import tempfile
import zipfile

from config import DATABASE_PATH, REPORT_DIR
from database import get_db, dict_from_row, now_str


BACKUP_DIR = os.path.join(REPORT_DIR, 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)


def record_operation_log(action, operator='', detail=''):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO operation_logs (action, operator, detail, created_at) VALUES (?, ?, ?, ?)',
        (action, operator or '', detail or '', now_str()),
    )
    conn.commit()


def list_operation_logs(limit=200):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM operation_logs ORDER BY created_at DESC, id DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    return [dict_from_row(row) for row in rows]


def build_backup_package():
    timestamp = now_str().replace(':', '-').replace('.', '-')
    backup_name = f'backup_{timestamp}'
    zip_path = os.path.join(BACKUP_DIR, f'{backup_name}.zip')

    db_copy_path = os.path.join(BACKUP_DIR, f'{backup_name}.db')
    conn = get_db()
    backup_conn = sqlite3.connect(db_copy_path)
    try:
        conn.backup(backup_conn)
    finally:
        backup_conn.close()

    logs_path = os.path.join(BACKUP_DIR, f'{backup_name}_logs.json')
    logs = list_operation_logs(limit=1000)
    with open(logs_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    manifest_path = os.path.join(BACKUP_DIR, f'{backup_name}_manifest.json')
    manifest = {
        'created_at': now_str(),
        'database_path': DATABASE_PATH,
        'database_file': os.path.basename(db_copy_path),
        'logs_file': os.path.basename(logs_path),
    }
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(db_copy_path, arcname=os.path.basename(db_copy_path))
        archive.write(logs_path, arcname=os.path.basename(logs_path))
        archive.write(manifest_path, arcname=os.path.basename(manifest_path))

    for path in (db_copy_path, logs_path, manifest_path):
        try:
            os.remove(path)
        except OSError:
            pass

    return zip_path
