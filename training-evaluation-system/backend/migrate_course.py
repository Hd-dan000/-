# -*- coding: utf-8 -*-
"""
课程体系迁移脚本
新表: course, teach, student_course
SQLite trainings 增加 course_id 字段
"""
import sys, os, json

# 设置路径
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

# 统一编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
else:
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

try:
    # ========== 1. MySQL 建表 ==========
    from database_mysql import get_db
    mdb = get_db()
    with mdb.cursor() as cursor:
        # 课程表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_name VARCHAR(100) NOT NULL,
                course_code VARCHAR(30) NOT NULL UNIQUE COMMENT '课程编号',
                semester VARCHAR(30) COMMENT '学期，如 2024-2025-1',
                credit INT DEFAULT 0 COMMENT '学分',
                school_id INT NOT NULL,
                college_id INT,
                teacher_id INT DEFAULT 0 COMMENT '主讲教师id',
                teacher_name VARCHAR(50) DEFAULT '' COMMENT '主讲教师名',
                description TEXT,
                is_active TINYINT(1) DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (school_id) REFERENCES schools(id),
                FOREIGN KEY (college_id) REFERENCES colleges(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程'
        """)
        print("[OK] 创建 course 表")

        # 授课关系：教师→课程→班级
        cursor.execute("""
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
        print("[OK] 创建 teach 表")

        # 学生选课
        cursor.execute("""
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
        print("[OK] 创建 student_course 表")

        # 给 submit_work 补 course_id 字段（如果缺）
        cursor.execute("SHOW COLUMNS FROM submit_work LIKE 'course_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE submit_work ADD COLUMN course_id INT DEFAULT 0 COMMENT '课程ID' AFTER training_id")
            print("[OK] submit_work 补 course_id 列")

        # ========== 2. 插入课程数据 ==========
        # 根据现有班级数据生成课程
        cursor.execute("SELECT * FROM classes ORDER BY id")
        classes = cursor.fetchall()

        courses_data = []
        for cls in classes:
            cid = cls['id']
            cname = cls['class_name']
            major = cls['major']
            college_id = cls['college_id']
            school_id = cls['school_id']
            grade = cls['grade']

            # 每个班级有2门课：专业核心课 + 公共课
            course1_code = f"{major[:2].upper()}{grade[-2:]}01"
            course2_code = f"GG{grade[-2:]}01"
            course1_name = f"{major}综合实训"
            course2_name = "软件工程基础"

            c1 = (course1_code, course1_name, school_id, college_id, cname, grade)
            c2 = (course2_code, course2_name, school_id, college_id, cname, grade)
            courses_data.append(c1)
            courses_data.append(c2)

        # 去重
        seen = set()
        unique_courses = []
        for c in courses_data:
            if c[0] not in seen:
                seen.add(c[0])
                unique_courses.append(c)

        # 删除旧数据再插入（幂等）
        cursor.execute("DELETE FROM student_course")
        cursor.execute("DELETE FROM teach")
        cursor.execute("DELETE FROM course")

        course_sql = """INSERT INTO course (course_code, course_name, school_id, college_id, teacher_id, teacher_name, semester)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        for code, name, sid, colid, _, grade in unique_courses:
            # 分配教师：每个课程关联到的班级的 teacherclasses 中第1个教师
            cursor.execute("""
                SELECT tc.teacher_id, t.name FROM teacherclasses tc 
                JOIN classes cl ON cl.id = tc.class_id 
                JOIN teachers t ON t.id = tc.teacher_id
                WHERE cl.college_id = %s LIMIT 1
            """, (colid,))
            teacher = cursor.fetchone()
            tid = teacher['teacher_id'] if teacher else 0
            tname = teacher['name'] if teacher else ''
            cursor.execute(course_sql, (code, name, sid, colid, tid, tname, f'{grade}-{int(grade)+1}-1'))

        print(f"[OK] 插入 {len(unique_courses)} 门课程")

        # ========== 3. 建立授课关系 ==========
        cursor.execute("SELECT * FROM course")
        all_courses = cursor.fetchall()

        teach_count = 0
        for course in all_courses:
            course_id = course['id']
            # 查找此课程对应的班级：同学院同年级
            cursor.execute("""
                SELECT cl.id FROM classes cl WHERE cl.college_id = %s AND cl.grade = %s
            """, (course['college_id'], course['semester'][:4] if course['semester'] else ''))
            course_classes = cursor.fetchall()

            for cc in course_classes:
                # 该班级的授课教师
                cursor.execute("SELECT teacher_id FROM teacherclasses WHERE class_id = %s", (cc['id'],))
                teachers = cursor.fetchall()
                for t in teachers:
                    try:
                        cursor.execute(
                            "INSERT INTO teach (course_id, teacher_id, class_id) VALUES (%s, %s, %s)",
                            (course_id, t['teacher_id'], cc['id'])
                        )
                        teach_count += 1
                    except Exception:
                        pass  # 唯一键冲突跳过

        print(f"[OK] 建立 {teach_count} 条授课关系")

        # ========== 4. 建立学生选课 ==========
        cursor.execute("SELECT * FROM students")
        all_students = cursor.fetchall()

        sc_count = 0
        for stu in all_students:
            student_id = stu['id']
            class_id = stu['class_id']

            # 该班级关联的所有课程
            cursor.execute("""
                SELECT DISTINCT t.course_id FROM teach t WHERE t.class_id = %s
            """, (class_id,))
            course_ids = cursor.fetchall()

            for cid_row in course_ids:
                try:
                    cursor.execute(
                        "INSERT INTO student_course (student_id, course_id) VALUES (%s, %s)",
                        (student_id, cid_row['course_id'])
                    )
                    sc_count += 1
                except Exception:
                    pass

        print(f"[OK] 建立 {sc_count} 条学生选课记录")

        mdb.commit()
        print("[OK] MySQL 事务提交")

    mdb.close()

    # ========== 5. SQLite trainings 表加 course_id ==========
    from database import get_db as get_sqlite3_db
    sdb = get_sqlite3_db()
    cursor = sdb.cursor()

    # 检查是否已有 course_id 列
    cursor.execute("PRAGMA table_info(trainings)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'course_id' not in cols:
        cursor.execute("ALTER TABLE trainings ADD COLUMN course_id INTEGER DEFAULT 0")
        print("[OK] SQLite trainings 表增加 course_id 列")
    else:
        print("[OK] SQLite trainings 已有 course_id 列")

    # 更新现有 training 关联课程
    cursor.execute("SELECT * FROM trainings")
    existing_trainings = cursor.fetchall()
    for row in existing_trainings:
        t = dict(row)
        course_name = t.get('course_name', '')
        if not course_name:
            continue

        # 在 MySQL 中查找匹配课程
        with mdb.cursor() as mc:
            mc.execute("SELECT id FROM course WHERE course_name LIKE %s OR course_code LIKE %s",
                       (f'%{course_name}%', f'%{course_name}%'))
            match = mc.fetchone()
            if match:
                cursor.execute("UPDATE trainings SET course_id = ? WHERE id = ?",
                               (match['id'], t['id']))
                print(f"  training id={t['id']} → course_id={match['id']} ({course_name})")

    sdb.commit()
    sdb.close()
    print("\n=== 迁移完成 ===")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\n错误: {e}")
