-- ============================================================
-- 创建数据库：信息
-- 包含：教师信息表 teachers、管理员表 admins、学生信息表 students
-- 适用： MySQL 5.7+ / 8.0
-- 字符集： utf8mb4
-- ============================================================

-- 0. 声明客户端字符集（解决中文库名乱码问题）
SET NAMES utf8mb4;

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS `信息`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `信息`;

-- 2. 教师信息表
CREATE TABLE IF NOT EXISTS `teachers` (
    `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `teacher_no`    VARCHAR(30)   NOT NULL UNIQUE         COMMENT '工号(唯一)',
    `name`          VARCHAR(50)   NOT NULL                COMMENT '姓名',
    `gender`        VARCHAR(10)   DEFAULT ''              COMMENT '性别',
    `title`         VARCHAR(50)   DEFAULT ''              COMMENT '职称',
    `department`    VARCHAR(100)  DEFAULT ''              COMMENT '所属院系/部门',
    `phone`         VARCHAR(20)   DEFAULT ''              COMMENT '联系电话',
    `email`         VARCHAR(100)  DEFAULT ''              COMMENT '邮箱',
    `password_hash` VARCHAR(255)  NOT NULL                COMMENT '密码哈希(SHA-256)',
    `is_active`     TINYINT(1)    DEFAULT 1               COMMENT '是否启用:1启用0禁用',
    `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师信息表';

-- 3. 管理员表
CREATE TABLE IF NOT EXISTS `admins` (
    `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `username`      VARCHAR(50)   NOT NULL UNIQUE         COMMENT '登录用户名(唯一)',
    `password_hash` VARCHAR(255)  NOT NULL                COMMENT '密码哈希(SHA-256)',
    `display_name`  VARCHAR(50)   NOT NULL                COMMENT '显示名',
    `role`          VARCHAR(20)   NOT NULL DEFAULT 'admin' COMMENT '角色: admin / super_admin',
    `last_login_at` DATETIME      DEFAULT NULL            COMMENT '最近登录时间',
    `is_active`     TINYINT(1)    DEFAULT 1               COMMENT '是否启用:1启用0禁用',
    `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- 4. 学生信息表
CREATE TABLE IF NOT EXISTS `students` (
    `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `student_no`    VARCHAR(30)   NOT NULL UNIQUE         COMMENT '学号(唯一)',
    `name`          VARCHAR(50)   NOT NULL                COMMENT '姓名',
    `gender`        VARCHAR(10)   DEFAULT ''              COMMENT '性别',
    `class_name`    VARCHAR(100)  DEFAULT ''              COMMENT '班级',
    `major`         VARCHAR(100)  DEFAULT ''              COMMENT '专业',
    `phone`         VARCHAR(20)   DEFAULT ''              COMMENT '联系电话',
    `email`         VARCHAR(100)  DEFAULT ''              COMMENT '邮箱',
    `password_hash` VARCHAR(255)  NOT NULL                COMMENT '密码哈希(SHA-256)',
    `is_active`     TINYINT(1)    DEFAULT 1               COMMENT '是否启用:1启用0禁用',
    `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';

-- 5. 学生信息初始数据
INSERT IGNORE INTO `students` (`student_no`, `name`, `gender`, `class_name`, `major`, `phone`, `email`, `password_hash`, `is_active`) VALUES
('202601001', '刘浩宇', '男', '软件2601', '软件技术', '13500135001', 'liuhy2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601002', '陈欣怡', '女', '软件2601', '软件技术', '13500135002', 'chenxy2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601003', '王泽楷', '男', '软件2601', '软件技术', '13500135003', 'wangzk2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601004', '林雨桐', '女', '软件2601', '软件技术', '13500135004', 'linyt2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601005', '周子豪', '男', '软件2602', '人工智能技术应用', '13500135005', 'zhouzh2602@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601006', '苏晚晴', '女', '软件2602', '人工智能技术应用', '13500135006', 'suwq2602@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601007', '吴俊峰', '男', '网络2601', '计算机网络技术', '13500135007', 'wujf2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 0),
('202601008', '徐若萱', '女', '网络2601', '计算机网络技术', '13500135008', 'xurx2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601009', '马浩然', '男', '大数据2601', '大数据技术', '13500135009', 'mahr2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1),
('202601010', '江诗瑶', '女', '大数据2601', '大数据技术', '13500135010', 'jiangsy2601@edu.cn', '7cf185410c34c42039e4d21f3f2b489a7d426188d7c043c5099d647c2802e191', 1);

-- ============================================================
-- 6. 学院信息表（新增）
-- ============================================================
CREATE TABLE IF NOT EXISTS `colleges` (
    `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `college_code`  VARCHAR(30)   NOT NULL UNIQUE         COMMENT '学院编号(唯一)',
    `college_name`  VARCHAR(100)  NOT NULL                COMMENT '学院名称',
    `description`   VARCHAR(255)  DEFAULT ''              COMMENT '学院简介',
    `is_active`     TINYINT(1)    DEFAULT 1               COMMENT '是否启用:1启用0禁用',
    `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学院信息表';

-- 7. 班级信息表（新增）
CREATE TABLE IF NOT EXISTS `classes` (
    `id`                INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `college_id`        INT           NOT NULL                COMMENT '所属学院ID',
    `class_code`        VARCHAR(30)   NOT NULL UNIQUE         COMMENT '班级编号(唯一)',
    `class_name`        VARCHAR(100)  NOT NULL                COMMENT '班级名称',
    `major`             VARCHAR(100)  DEFAULT ''              COMMENT '所属专业',
    `grade`             VARCHAR(20)   DEFAULT ''              COMMENT '年级',
    `create_teacher_id` INT           NOT NULL                COMMENT '创建该班级的教师ID',
    `teaching_status`   VARCHAR(20)   DEFAULT 'not_started'   COMMENT '开课状态:not_started未开课/in_progress开课中/ended已结课',
    `is_active`         TINYINT(1)    DEFAULT 1               COMMENT '是否启用:1启用0禁用',
    `created_at`        DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_college_id` (`college_id`),
    KEY `idx_create_teacher_id` (`create_teacher_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级信息表';

-- 8. 教师-班级关联表（多对多）
CREATE TABLE IF NOT EXISTS `teacherclasses` (
    `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `teacher_id`    INT           NOT NULL                COMMENT '教师ID',
    `class_id`      INT           NOT NULL                COMMENT '班级ID',
    `role`          VARCHAR(50)   DEFAULT '指导教师'      COMMENT '教师角色: 班主任/授课教师/实训指导',
    `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_teacher_class` (`teacher_id`, `class_id`),
    KEY `idx_class_id` (`class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师-班级关联表';

-- ============================================================
-- 9. 现有表结构调整
-- ============================================================

-- 9.1 教师表补充学院关联
ALTER TABLE `teachers`
ADD COLUMN `college_id` INT NOT NULL DEFAULT 0 COMMENT '所属学院ID' AFTER `id`,
ADD INDEX `idx_college_id` (`college_id`);

-- 9.2 学生表补充班级关联
ALTER TABLE `students`
ADD COLUMN `class_id` INT NOT NULL DEFAULT 0 COMMENT '所属班级ID' AFTER `id`,
ADD INDEX `idx_class_id` (`class_id`);