"""更新 teachers 表中所有教师的密码为工号末尾4位数（SHA-256 哈希）"""
import hashlib
import pymysql
import pymysql.cursors
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def main():
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with conn.cursor() as cursor:
            # 查询所有教师
            cursor.execute("SELECT id, teacher_no, name FROM teachers ORDER BY id")
            teachers = cursor.fetchall()

            if not teachers:
                print("未找到任何教师记录")
                return

            print(f"共找到 {len(teachers)} 位教师:\n")

            updated = 0
            for teacher in teachers:
                tid = teacher['id']
                teacher_no = teacher['teacher_no']
                name = teacher['name']

                # 取工号末尾4位作为密码
                new_password = teacher_no[-4:] if len(teacher_no) >= 4 else teacher_no
                new_hash = hash_password(new_password)

                # 更新密码哈希
                cursor.execute(
                    "UPDATE teachers SET password_hash = %s WHERE id = %s",
                    (new_hash, tid),
                )

                print(f"  [{name}] 工号: {teacher_no} → 密码: {new_password}")
                updated += cursor.rowcount

        conn.commit()
        print(f"\n成功更新 {updated} 位教师的密码")

    finally:
        conn.close()


if __name__ == '__main__':
    main()