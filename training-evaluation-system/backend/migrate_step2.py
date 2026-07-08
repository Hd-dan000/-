# -*- coding: utf-8 -*-
"""Step 2: 插入课程、授课关系、学生选课数据"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', database='信息',
                       charset='utf8mb4', connect_timeout=10)
conn.autocommit(False)

try:
    with conn.cursor(pymysql.cursors.DictCursor) as c:
        # 1. 读取所有班级
        c.execute("SELECT id, class_name, major, college_id, school_id, grade FROM classes ORDER BY id")
        classes = c.fetchall()
        print(f'读取 {len(classes)} 个班级')

        # 2. 为每个班级生成2门课（专业核心+公共基础）
        course_inserts = []
        seen_codes = set()
        for cls in classes:
            cid = cls['id']
            cname = cls['class_name']
            major = cls['major'] or '通用'
            college_id = cls['college_id']
            school_id = cls['school_id']
            grade = cls['grade'] or '2024'

            # 课程1: 专业综合实训
            prefix = major[:2].upper() if major else 'ZY'
            code1 = f'{prefix}{grade[-2:]}ST01'
            name1 = f'{major}综合实训'
            if code1 not in seen_codes:
                seen_codes.add(code1)
                course_inserts.append((code1, name1, school_id, college_id, grade))

            # 课程2: 软件工程基础
            code2 = f'GG{grade[-2:]}GC01'
            name2 = '软件工程基础'
            if code2 not in seen_codes:
                seen_codes.add(code2)
                course_inserts.append((code2, name2, school_id, college_id, grade))

        print(f'需创建 {len(course_inserts)} 门课程')

        # 清空旧数据（幂等）
        c.execute("DELETE FROM student_course")
        c.execute("DELETE FROM teach")
        c.execute("DELETE FROM course WHERE is_active=1")
        c.execute("ALTER TABLE course AUTO_INCREMENT = 1")

        # 插入课程 - 需要找教师
        for code, name, sid, colid, grade in course_inserts:
            c.execute("""
                SELECT tc.teacher_id, t.name FROM teacherclasses tc
                JOIN classes cl ON cl.id = tc.class_id
                JOIN teachers t ON t.id = tc.teacher_id
                WHERE cl.college_id = %s LIMIT 1
            """, (colid,))
            teacher = c.fetchone()
            tid = teacher['teacher_id'] if teacher else 0
            tname = teacher['name'] if teacher else ''

            semester = f'{grade}-{int(grade)+1}-1'
            c.execute(
                "INSERT INTO course (course_code, course_name, school_id, college_id, teacher_id, teacher_name, semester) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (code, name, sid, colid, tid, tname, semester)
            )
        print(f'[OK] 插入 {len(course_inserts)} 门课程')

        # 3. 建立授课关系
        c.execute("SELECT id, college_id, semester, teacher_id FROM course")
        all_courses = c.fetchall()
        teach_cnt = 0
        assigned_pairs = set()
        for crs in all_courses:
            crs_id = crs['id']
            colid = crs['college_id']
            sem = crs['semester'] or ''
            grade = sem[:4] if len(sem) >= 4 else '2024'

            # 找该学院同年级班级
            c.execute("SELECT id FROM classes WHERE college_id = %s AND grade = %s", (colid, grade))
            class_rows = c.fetchall()

            for cr in class_rows:
                class_id = cr['id']
                # 该班级的教师
                c.execute("SELECT teacher_id FROM teacherclasses WHERE class_id = %s", (class_id,))
                teachers = c.fetchall()
                for te in teachers:
                    tid = te['teacher_id']
                    pair = (crs_id, tid, class_id)
                    if pair not in assigned_pairs:
                        assigned_pairs.add(pair)
                        c.execute(
                            "INSERT INTO teach (course_id, teacher_id, class_id) VALUES (%s,%s,%s)",
                            (crs_id, tid, class_id)
                        )
                        teach_cnt += 1
        print(f'[OK] 建立 {teach_cnt} 条授课关系')

        # 4. 建立学生选课
        c.execute("SELECT id, class_id FROM students")
        all_students = c.fetchall()
        sc_cnt = 0
        assigned_sc = set()
        for stu in all_students:
            sid = stu['id']
            class_id = stu['class_id']

            c.execute("SELECT DISTINCT course_id FROM teach WHERE class_id = %s", (class_id,))
            course_ids = c.fetchall()
            for ci in course_ids:
                coid = ci['course_id']
                pair = (sid, coid)
                if pair not in assigned_sc:
                    assigned_sc.add(pair)
                    c.execute("INSERT INTO student_course (student_id, course_id) VALUES (%s,%s)",
                              (sid, coid))
                    sc_cnt += 1
        print(f'[OK] 建立 {sc_cnt} 条学生选课记录')

        conn.commit()
        print('=== Step 2 完成 ===')

except Exception as e:
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    conn.close()
