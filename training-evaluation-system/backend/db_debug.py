# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = open(1, 'w', encoding='utf-8', closefd=False)

# 1. SQLite
from database import get_db as get_sqlite_db
db = get_sqlite_db()
c = db.cursor()

c.execute("SELECT sql FROM sqlite_master WHERE name='trainings'")
ddl = c.fetchone()
print('=== trainings 建表SQL ===')
print(ddl[0] if ddl else 'No table found')

c.execute("PRAGMA table_info(trainings)")
rows = c.fetchall()
print('\n=== trainings 表结构(pragma) ===')
for r in rows:
    print(' ', dict(r))

c.execute("SELECT * FROM trainings LIMIT 5")
rows = c.fetchall()
print('\n=== trainings 数据前5条 ===')
for r in rows:
    print(' ', dict(r))

c.execute("PRAGMA table_info(submissions)")
rows = c.fetchall()
print('\n=== submissions 表结构 ===')
for r in rows:
    print(' ', dict(r))

# 2. MySQL 表结构 & 数据
from database_mysql import get_db
mdb = get_db()
with mdb.cursor() as c2:
    c2.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='信息'")
    print('\n=== MySQL 所有表 ===')
    for r in c2.fetchall():
        print(' ', r['TABLE_NAME'])

    for tname in ['teachers', 'students', 'classes', 'teacherclasses']:
        c2.execute(f"SELECT COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='信息' AND TABLE_NAME='{tname}'")
        rows = c2.fetchall()
        if rows:
            print(f'\n=== {tname} ===')
            for r in rows:
                print(f'  {r["COLUMN_NAME"]:20s} {r["COLUMN_TYPE"]}')
    
    # 数据量
    for tname in ['teachers', 'students', 'classes', 'teacherclasses', 'submit_work']:
        c2.execute(f"SELECT COUNT(*) as cnt FROM {tname}")
        cnt = c2.fetchone()['cnt']
        print(f'\n{tname}: {cnt} 条记录')
        
    # teacherclasses数据
    c2.execute("SELECT * FROM teacherclasses")
    print('\n=== teacherclasses 数据 ===')
    for r in c2.fetchall():
        print(' ', r)
