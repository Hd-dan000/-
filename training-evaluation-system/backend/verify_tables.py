# -*- coding: utf-8 -*-
import pymysql, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', charset='utf8mb4', database='信息')
cursor = conn.cursor()

tables = ['schools','colleges','classes','students','teachers','teacherclasses','admins']
for t in tables:
    cursor.execute(f'DESCRIBE {t}')
    cols = cursor.fetchall()
    print(f'\n=== {t} ({len(cols)} 列) ===')
    for c in cols:
        field, field_type, nullable, key, default, extra = c
        print(f'  {field:25} {field_type:20} {key:5} {extra}')

cursor.close()
conn.close()
