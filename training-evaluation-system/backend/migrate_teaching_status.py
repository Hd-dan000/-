# -*- coding: utf-8 -*-
"""迁移脚本：为 classes 表添加 teaching_status 字段"""
import sys
from database_mysql import get_db


def migrate():
    db = get_db()
    try:
        with db.cursor() as cursor:
            # 检查字段是否已存在
            cursor.execute("SHOW COLUMNS FROM `classes` LIKE 'teaching_status'")
            if cursor.fetchone():
                print("teaching_status 字段已存在，跳过迁移")
                return

            cursor.execute("""
                ALTER TABLE `classes`
                ADD COLUMN `teaching_status` VARCHAR(20) DEFAULT 'not_started'
                    COMMENT '开课状态:not_started未开课/in_progress开课中/ended已结课'
                AFTER `create_teacher_id`
            """)
            db.commit()
            print("迁移成功：已添加 teaching_status 字段")
    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    migrate()
