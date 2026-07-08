# -*- coding: utf-8 -*-
"""将 course 表课程名称更新为 5 个企业级实训项目名称。

说明：
- 仅修改 course.course_name，保留 course_code、semester、teacher_id、teacher_name
  以及 teach、student_course 等关联数据不变。
- 按 id 顺序循环写入 5 个实训项目名。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_mysql import get_db

PROJECT_NAMES = [
    '“智聘”企业级人力资源管理系统（HRMS）',
    '“鲜速达”生鲜电商小程序',
    '智慧校园统一数据可视化大屏',
    '云物业收费与服务 SaaS 系统',
    '智能家居设备管控平台',
]


def update():
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT id FROM course ORDER BY id")
            ids = [row['id'] for row in cursor.fetchall()]
            if not ids:
                print('course 表中没有记录')
                return

            for i, cid in enumerate(ids):
                name = PROJECT_NAMES[i % len(PROJECT_NAMES)]
                cursor.execute(
                    "UPDATE course SET course_name = %s WHERE id = %s",
                    (name, cid)
                )
                print(f'course id={cid} -> {name}')

            db.commit()
            print(f'\n共更新 {len(ids)} 条课程记录')
    finally:
        db.close()


if __name__ == '__main__':
    update()
