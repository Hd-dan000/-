# -*- coding: utf-8 -*-
"""验证课程体系迁移结果"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import pymysql
from database import get_db as get_sqlite3_db

# MySQL 验证
conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', database='信息',
                       charset='utf8mb4', connect_timeout=10)
with conn.cursor(pymysql.cursors.DictCursor) as c:
    c.execute("SELECT COUNT(*) as cnt FROM course")
    print(f'course 表: {c.fetchone()["cnt"]} 门课程')
    c.execute("SELECT * FROM course")
    for r in c.fetchall():
        print(f'  [{r["course_code"]}] {r["course_name"]} (semester={r["semester"]}, teacher={r["teacher_name"]})')

    c.execute("SELECT COUNT(*) as cnt FROM teach")
    print(f'\nteach 表: {c.fetchone()["cnt"]} 条授课关系')

    c.execute("SELECT COUNT(*) as cnt FROM student_course")
    print(f'student_course 表: {c.fetchone()["cnt"]} 条选课记录')

    # 检查某学生的课程
    c.execute("""
        SELECT s.name, s.student_no, c.course_name, c.course_code
        FROM student_course sc
        JOIN students s ON s.id = sc.student_id
        JOIN course c ON c.id = sc.course_id
        LIMIT 10
    """)
    print('\n  前 10 条选课记录:')
    for r in c.fetchall():
        print(f'  {r["student_name"]}({r["student_no"]}) → {r["course_name"]}')

conn.close()

# SQLite 验证
sdb = get_sqlite3_db()
c = sdb.cursor()
c.execute("SELECT id, title, course_id, course_name FROM trainings")
print('\n=== SQLite trainings ===')
for r in c.fetchall():
    d = dict(r)
    print(f'  id={d["id"]} title={d["title"]} course_id={d["course_id"]}')
sdb.close()

print('\n=== 验证完成 ===')
