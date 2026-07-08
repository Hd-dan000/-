# -*- coding: utf-8 -*-
"""创建 submit_work 表（MySQL 信息库）"""
import pymysql
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', charset='utf8mb4', database='信息')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS submit_work (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    student_id INT NOT NULL COMMENT '学生ID(students.id)',
    student_no VARCHAR(30) NOT NULL COMMENT '学号',
    student_name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    class_id INT NOT NULL COMMENT '所属班级ID',
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    training_id INT NOT NULL COMMENT '实训任务ID',
    training_title VARCHAR(200) NOT NULL DEFAULT '' COMMENT '实训任务名称',
    file_path VARCHAR(500) NOT NULL COMMENT '文件相对路径(相对upload/homework)',
    file_original_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_extension VARCHAR(20) NOT NULL COMMENT '文件后缀',
    file_size BIGINT NOT NULL DEFAULT 0 COMMENT '文件大小(字节)',
    content_type VARCHAR(100) DEFAULT '' COMMENT 'MIME类型',
    status VARCHAR(20) DEFAULT 'submitted' COMMENT '状态: submitted/evaluated',
    teacher_score DECIMAL(5,1) DEFAULT NULL COMMENT '教师评分',
    teacher_comment TEXT COMMENT '教师评语',
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    reviewed_at DATETIME DEFAULT NULL COMMENT '批阅时间',
    PRIMARY KEY (id),
    KEY idx_student_id (student_id),
    KEY idx_class_id (class_id),
    KEY idx_training_id (training_id),
    KEY idx_class_training (class_id, training_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='作业提交表'
""")
conn.commit()
print('submit_work 表创建成功 ✅')
cursor.close()
conn.close()
