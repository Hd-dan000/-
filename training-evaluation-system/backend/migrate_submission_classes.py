"""
为已有 submissions 记录回填 class_id / class_name。
匹配规则：优先按 student_id（即学号 student_no）匹配 MySQL students 表；
        学号为空时按 student_name 兜底匹配。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, dict_from_row, now_str, init_db
from database_mysql import get_db as get_mysql_db


def migrate():
    init_db()  # 确保新列已通过 ALTER TABLE 迁移到现有数据库
    sqlite_conn = get_db()
    sqlite_cursor = sqlite_conn.cursor()

    sqlite_cursor.execute(
        "SELECT id, student_id, student_name FROM submissions "
        "WHERE class_id IS NULL OR class_id = 0 OR class_name IS NULL OR class_name = ''"
    )
    submissions = [dict_from_row(row) for row in sqlite_cursor.fetchall()]

    if not submissions:
        print("没有需要迁移的提交记录")
        return

    mysql_db = get_mysql_db()
    mysql_cursor = mysql_db.cursor(dictionary=True)

    migrated = 0
    fallback = 0

    for s in submissions:
        student_no = (s.get('student_id') or '').strip()
        student_name = (s.get('student_name') or '').strip()
        class_id = None
        class_name = None

        # 优先按学号匹配
        if student_no:
            mysql_cursor.execute(
                "SELECT class_id, class_name FROM students WHERE student_no = %s AND is_active = 1 LIMIT 1",
                (student_no,)
            )
            stu = mysql_cursor.fetchone()
            if stu:
                class_id = stu['class_id']
                class_name = stu['class_name']

        # 兜底按姓名匹配
        if class_id is None and student_name:
            mysql_cursor.execute(
                "SELECT class_id, class_name FROM students WHERE name = %s AND is_active = 1 LIMIT 1",
                (student_name,)
            )
            stu = mysql_cursor.fetchone()
            if stu:
                class_id = stu['class_id']
                class_name = stu['class_name']
                fallback += 1

        if class_id is not None:
            sqlite_cursor.execute(
                """
                UPDATE submissions
                SET class_id = ?, class_name = ?, updated_at = ?
                WHERE id = ?
                """,
                (class_id or 0, class_name or '', now_str(), s['id'])
            )
            migrated += 1

    sqlite_conn.commit()
    print(f"共扫描 {len(submissions)} 条记录，成功迁移 {migrated} 条（其中姓名兜底 {fallback} 条）")


if __name__ == '__main__':
    migrate()
