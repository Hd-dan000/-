# -*- coding: utf-8 -*-
import sys, io, json as json_mod
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database_mysql import get_db

teacher_id = 1
db = get_db()
cursor = db.cursor()

try:
    cursor.execute('SELECT class_id FROM teacherclasses WHERE teacher_id = %s', (teacher_id,))
    rows = cursor.fetchall()
    print('rows:', rows)
    teacher_class_ids = [r['class_id'] for r in rows]
    print('teacher_class_ids:', teacher_class_ids)

    if teacher_class_ids:
        ids_str = ','.join(str(c) for c in teacher_class_ids)
        where = 'sw.class_id IN (' + ids_str + ')'
        sql = """
            SELECT sw.*, tc.teacher_id 
            FROM submit_work sw
            JOIN teacherclasses tc ON tc.class_id = sw.class_id AND tc.teacher_id = %s
            WHERE %s
            ORDER BY sw.submitted_at DESC
        """ % ('%s', where)
        print('SQL:', sql)
        cursor.execute(sql, (teacher_id,))
        result = cursor.fetchall()
        print('Result count:', len(result))
finally:
    cursor.close()
