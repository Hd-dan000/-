import sqlite3
import json
import random
from datetime import datetime

random.seed(42)

# Class 1 students (first 5)
students = [
    ('20240161', '唐洋宇'),
    ('20240162', '于斌'),
    ('20240163', '易刚宇'),
    ('20240164', '白轩'),
    ('20240165', '胡浩志'),
]

conn = sqlite3.connect('data.db')
cur = conn.cursor()

now = datetime.now().isoformat()
file_path = 'uploads/training_3/test_doc.txt'
files = json.dumps([{'filename': 'test_doc.txt', 'path': file_path, 'size': 16}], ensure_ascii=False)

def make_eval_detail(doc, code, logic, innovation):
    return {
        'indicator_summary': [
            {'name': '文档质量', 'score': doc},
            {'name': '代码规范', 'score': code},
            {'name': '逻辑能力', 'score': logic},
            {'name': '创新度', 'score': innovation},
        ],
        'category_evaluation': {
            'document': {'score': doc},
            'code': {'score': code},
            'ui': {'score': round((doc + code) / 2, 1)},
        },
        'overall_score': round(doc * 0.3 + code * 0.35 + logic * 0.25 + innovation * 0.1, 1),
    }

for sno, name in students:
    doc = round(random.uniform(65, 95), 1)
    code = round(random.uniform(60, 92), 1)
    logic = round(random.uniform(62, 94), 1)
    innovation = round(random.uniform(50, 88), 1)
    eval_detail = make_eval_detail(doc, code, logic, innovation)
    final_score = eval_detail['overall_score']
    cur.execute('''
        INSERT OR REPLACE INTO submissions
        (training_id, student_name, student_id, class_id, class_name, files, parsed_content,
         status, final_score, evaluation_detail, category_teacher_scores, created_at, updated_at)
        VALUES (
            3, ?, ?, 1, 'SOFT2401', ?, 'test content for growth analysis',
            'evaluated', ?, ?, '{}', ?, ?
        )
    ''', (name, sno, files, final_score, json.dumps(eval_detail, ensure_ascii=False), now, now))

conn.commit()

# Verify
cur.execute("SELECT student_id, student_name, class_id, status, final_score FROM submissions WHERE training_id=3 AND class_id=1")
for row in cur.fetchall():
    print(row)

conn.close()
print('Class 1 growth test data seeded.')
