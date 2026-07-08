# -*- coding: utf-8 -*-
"""Step 1: 创建 teach + student_course 表，submit_work 补 course_id"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', database='信息',
                       charset='utf8mb4', connect_timeout=5, read_timeout=30)

with conn.cursor() as c:
    c.execute("""
        CREATE TABLE IF NOT EXISTS teach (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            teacher_id INT NOT NULL,
            class_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES course(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            UNIQUE KEY uk_teach (course_id, teacher_id, class_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='授课关系'
    """)
    print('[OK] teach 表')

    c.execute("""
        CREATE TABLE IF NOT EXISTS student_course (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_id) REFERENCES course(id),
            UNIQUE KEY uk_stu_course (student_id, course_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生选课'
    """)
    print('[OK] student_course 表')

    c.execute("SHOW COLUMNS FROM submit_work LIKE 'course_id'")
    if not c.fetchone():
        c.execute("ALTER TABLE submit_work ADD COLUMN course_id INT DEFAULT 0 COMMENT '课程ID' AFTER training_id")
        print('[OK] submit_work 补 course_id 列')
    else:
        print('[-] submit_work 已有 course_id 列')

conn.commit()
conn.close()
print('=== Step 1 完成 ===')
