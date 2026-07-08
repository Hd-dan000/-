# -*- coding: utf-8 -*-
"""Step 3: SQLite trainings 关联 course_id + 更新 submit_work.course_id"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import pymysql

# SQLite trainings 加 course_id
from database import get_db as get_sqlite3_db
sdb = get_sqlite3_db()
c = sdb.cursor()

c.execute("PRAGMA table_info(trainings)")
cols = [row[1] for row in c.fetchall()]
if 'course_id' not in cols:
    c.execute("ALTER TABLE trainings ADD COLUMN course_id INTEGER DEFAULT 0")
    print('[OK] SQLite trainings 加 course_id 列')
else:
    print('[-] SQLite trainings 已有 course_id')

# 查询所有 trainings
c.execute("SELECT * FROM trainings")
trainings = [dict(row) for row in c.fetchall()]
print(f'SQLite 有 {len(trainings)} 个实训任务')

# 连接到 MySQL 查找课程
conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', database='信息',
                       charset='utf8mb4', connect_timeout=10)
updated = 0
for t in trainings:
    course_name = t.get('course_name', '')
    tid = t['id']
    if not course_name:
        c.execute("UPDATE trainings SET course_id = 0 WHERE id = ?", (tid,))
        continue

    # 查找 MySQL 中匹配的课程
    with conn.cursor(pymysql.cursors.DictCursor) as mc:
        mc.execute("SELECT id FROM course WHERE course_name LIKE %s", (f'%{course_name}%',))
        match = mc.fetchone()
        if match:
            c.execute("UPDATE trainings SET course_id = ? WHERE id = ?", (match['id'], tid))
            updated += 1
            print(f'  training id={tid} "{course_name}" → course_id={match["id"]}')
        else:
            print(f'  training id={tid} "{course_name}" → 未匹配课程')

sdb.commit()
sdb.close()
print(f'[OK] 更新 {updated} 个训练关联课程')

# submit_work 无数据，跳过 course_id 同步
print('[-] submit_work 无数据，跳过 course_id 同步')

conn.commit()
conn.close()
print('=== Step 3 完成 ===')
