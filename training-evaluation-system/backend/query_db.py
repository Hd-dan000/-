import sqlite3
conn = sqlite3.connect(r'F:\xiangmu\training-evaluation-system\backend\data.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('数据库表：')
for t in tables:
    print('  -', t[0])

# 查看每个表的结构
for t in tables:
    print(f'\n=== 表: {t[0]} ===')
    cursor.execute(f"PRAGMA table_info({t[0]})")
    cols = cursor.fetchall()
    for c in cols:
        print(f'  {c[1]} ({c[2]})')

# 查找赵明老师教授的课程
print('\n=== 查找赵明老师 ===')
cursor.execute("SELECT * FROM trainings WHERE teacher_name LIKE '%赵明%'")
rows = cursor.fetchall()
if rows:
    print('赵明老师教授的课程：')
    for r in rows:
        print(f'  课程ID: {r[0]}')
        print(f'  课程名称: {r[3]}')
        print(f'  实训项目: {r[1]}')
        print(f'  教师: {r[4]}')
        print(f'  状态: {r[7]}')
        print('---')
else:
    print('未找到赵明老师的记录')

# 查看所有教师名称（去重）
print('\n=== 所有教师列表 ===')
cursor.execute("SELECT DISTINCT teacher_name FROM trainings WHERE teacher_name IS NOT NULL")
teachers = cursor.fetchall()
for t in teachers:
    print(f'  - {t[0]}')

# 查看所有课程
print('\n=== 所有课程列表 ===')
cursor.execute("SELECT id, course_name, teacher_name, title FROM trainings")
courses = cursor.fetchall()
for c in courses:
    print(f'  ID:{c[0]} | 课程:{c[1]} | 教师:{c[2]} | 项目:{c[3]}')

conn.close()
