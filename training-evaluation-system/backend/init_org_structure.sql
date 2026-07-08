-- ============================================================
-- 组织架构数据表：学校 → 学院 → 班级 → 学生
-- 适用： MySQL 5.7+ / 8.0
-- 字符集： utf8mb4
-- ============================================================

SET NAMES utf8mb4;

-- 1. 学校信息表（新增，顶层）
CREATE TABLE IF NOT EXISTS `schools` (
    `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键',
    `school_code`   VARCHAR(30)   NOT NULL UNIQUE         COMMENT '学校编号(唯一)',
    `school_name`   VARCHAR(100)  NOT NULL                COMMENT '学校名称',
    `province`      VARCHAR(50)   DEFAULT ''              COMMENT '所在省份',
    `city`          VARCHAR(50)   DEFAULT ''              COMMENT '所在城市',
    `address`       VARCHAR(255)  DEFAULT ''              COMMENT '详细地址',
    `contact_phone` VARCHAR(20)   DEFAULT ''              COMMENT '联系电话',
    `description`   VARCHAR(500)  DEFAULT ''              COMMENT '学校简介',
    `is_active`     TINYINT(1)    DEFAULT 1               COMMENT '是否启用:1启用0禁用',
    `created_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学校信息表';

-- 2. 学院信息表（已有，此处补充 school_id 外键，如需多学校支持）
ALTER TABLE `colleges` 
ADD COLUMN `school_id` INT NOT NULL DEFAULT 1 COMMENT '所属学校ID' AFTER `id`,
ADD INDEX `idx_school_id` (`school_id`);

-- 3. 班级信息表（补充 school_id 冗余字段，便于跨层级查询）
ALTER TABLE `classes`
ADD COLUMN `school_id` INT NOT NULL DEFAULT 1 COMMENT '所属学校ID(冗余)' AFTER `college_id`,
ADD INDEX `idx_school_id` (`school_id`);

-- 4. 学生表（补充 school_id 冗余字段）
ALTER TABLE `students`
ADD COLUMN `school_id` INT NOT NULL DEFAULT 1 COMMENT '所属学校ID(冗余)' AFTER `class_id`,
ADD INDEX `idx_school_id` (`school_id`);

-- 5. 教师表（补充 school_id 冗余字段）
ALTER TABLE `teachers`
ADD COLUMN `school_id` INT NOT NULL DEFAULT 1 COMMENT '所属学校ID(冗余)' AFTER `college_id`,
ADD INDEX `idx_school_id` (`school_id`);
