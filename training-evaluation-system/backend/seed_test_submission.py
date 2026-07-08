import sqlite3
import json
import os
from datetime import datetime

conn = sqlite3.connect('data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 激活训练 3 并绑定班级
cur.execute("UPDATE trainings SET status = 'not_started' WHERE id = 3")
cur.execute("DELETE FROM training_classes WHERE training_id = 3 AND class_id = 3")
cur.execute("INSERT INTO training_classes (training_id, class_id, class_name) VALUES (3, 3, 'AI2401')")

file_path = os.path.abspath('uploads/training_3/test_doc.txt')
files = json.dumps([{'filename': 'test_doc.txt', 'path': file_path, 'size': 16}], ensure_ascii=False)
now = datetime.now().isoformat()

cur.execute("""
    INSERT OR REPLACE INTO submissions (id, training_id, student_name, student_id, class_id, class_name, files, parsed_content, status, created_at, updated_at)
    VALUES (
        (SELECT id FROM submissions WHERE training_id = 3 AND student_id = '20240001'),
        3, '孟峰', '20240001', 3, 'AI2401', ?, 'test content', 'submitted', ?, ?
    )
""", (files, now, now))
conn.commit()
cur.execute("SELECT id FROM submissions WHERE training_id = 3 AND student_id = '20240001'")
print('submission id', cur.fetchone()[0])
