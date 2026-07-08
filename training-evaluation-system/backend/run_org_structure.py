# -*- coding: utf-8 -*-
import pymysql
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', charset='utf8mb4', database='信息')
cursor = conn.cursor()

# 1. 创建 schools 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS schools (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    school_code VARCHAR(30) NOT NULL UNIQUE COMMENT '学校编号(唯一)',
    school_name VARCHAR(100) NOT NULL COMMENT '学校名称',
    province VARCHAR(50) DEFAULT '' COMMENT '所在省份',
    city VARCHAR(50) DEFAULT '' COMMENT '所在城市',
    address VARCHAR(255) DEFAULT '' COMMENT '详细地址',
    contact_phone VARCHAR(20) DEFAULT '' COMMENT '联系电话',
    description VARCHAR(500) DEFAULT '' COMMENT '学校简介',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学校信息表'
""")
conn.commit()
print('[1] schools OK')

# 切到「信息」库
cursor.execute('USE `信息`')
conn.commit()

# 2-5. ALTER TABLE（为现有表补充 school_id）
alts = [
    ("ALTER TABLE colleges ADD COLUMN school_id INT NOT NULL DEFAULT 1 COMMENT '所属学校ID' AFTER id, ADD INDEX idx_school_id (school_id)", "colleges"),
    ("ALTER TABLE classes ADD COLUMN school_id INT NOT NULL DEFAULT 1 COMMENT '所属学校ID' AFTER college_id, ADD INDEX idx_school_id (school_id)", "classes"),
    ("ALTER TABLE students ADD COLUMN school_id INT NOT NULL DEFAULT 1 COMMENT '所属学校ID' AFTER class_id, ADD INDEX idx_school_id (school_id)", "students"),
    ("ALTER TABLE teachers ADD COLUMN school_id INT NOT NULL DEFAULT 1 COMMENT '所属学校ID' AFTER college_id, ADD INDEX idx_school_id (school_id)", "teachers"),
]

for i, (sql, table) in enumerate(alts, 2):
    try:
        cursor.execute(sql)
        conn.commit()
        print(f'[{i}] {table} school_id OK')
    except Exception as e:
        print(f'[{i}] {table} ERR: {e}')

cursor.close()
conn.close()
print('ALL Done')
