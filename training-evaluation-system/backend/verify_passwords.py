"""验证教师密码更新结果"""
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
            cursor.execute("SELECT id, teacher_no, name, password_hash FROM teachers ORDER BY id")
            teachers = cursor.fetchall()

            print(f"{'姓名':<8} {'工号':<10} {'预期密码':<10} {'密码验证':<10}")
            print("-" * 40)

            all_ok = True
            for t in teachers:
                expected_pwd = t['teacher_no'][-4:] if len(t['teacher_no']) >= 4 else t['teacher_no']
                expected_hash = hash_password(expected_pwd)
                matched = "✓ 通过" if t['password_hash'] == expected_hash else "✗ 不匹配"
                if t['password_hash'] != expected_hash:
                    all_ok = False
                print(f"{t['name']:<8} {t['teacher_no']:<10} {expected_pwd:<10} {matched:<10}")

            print(f"\n{'='*40}")
            print(f"验证结果: {'全部通过' if all_ok else '存在不匹配记录'}")

    finally:
        conn.close()


if __name__ == '__main__':
    main()