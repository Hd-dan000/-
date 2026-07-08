# -*- coding: utf-8 -*-
"""补全 init_info_db.sql 中遗漏的 CREATE 和 ALTER TABLE"""
import pymysql
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', charset='utf8mb4', database='信息')
cursor = conn.cursor()

# 1. 创建 colleges 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS colleges (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    college_code VARCHAR(30) NOT NULL UNIQUE COMMENT '学院编号(唯一)',
    college_name VARCHAR(100) NOT NULL COMMENT '学院名称',
    description VARCHAR(255) DEFAULT '' COMMENT '学院简介',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学院信息表'
""")
conn.commit()
print('[1] colleges OK')

# 2. 创建 classes 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS classes (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    college_id INT NOT NULL COMMENT '所属学院ID',
    class_code VARCHAR(30) NOT NULL UNIQUE COMMENT '班级编号(唯一)',
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    major VARCHAR(100) DEFAULT '' COMMENT '所属专业',
    grade VARCHAR(20) DEFAULT '' COMMENT '年级',
    create_teacher_id INT NOT NULL COMMENT '创建该班级的教师ID',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_college_id (college_id),
    KEY idx_create_teacher_id (create_teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级信息表'
""")
conn.commit()
print('[2] classes OK')

# 3. 创建 teacherclasses 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS teacherclasses (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    teacher_id INT NOT NULL COMMENT '教师ID',
    class_id INT NOT NULL COMMENT '班级ID',
    role VARCHAR(50) DEFAULT '指导教师' COMMENT '教师角色',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_teacher_class (teacher_id, class_id),
    KEY idx_class_id (class_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师-班级关联表'
""")
conn.commit()
print('[3] teacherclasses OK')

# 4. ALTER teachers: 添加 college_id
try:
    cursor.execute("ALTER TABLE teachers ADD COLUMN college_id INT NOT NULL DEFAULT 0 COMMENT '所属学院ID' AFTER id, ADD INDEX idx_college_id (college_id)")
    conn.commit()
    print('[4] teachers college_id OK')
except Exception as e:
    print(f'[4] teachers college_id: {e}')

# 5. ALTER students: 添加 class_id
try:
    cursor.execute("ALTER TABLE students ADD COLUMN class_id INT NOT NULL DEFAULT 0 COMMENT '所属班级ID' AFTER id, ADD INDEX idx_class_id (class_id)")
    conn.commit()
    print('[5] students class_id OK')
except Exception as e:
    print(f'[5] students class_id: {e}')

cursor.close()
conn.close()
print('init_info_db 补全完成！')
