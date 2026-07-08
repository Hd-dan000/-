"""MySQL 数据库初始化脚本
向「信息」库的 admins 表写入默认超级管理员账号

用法:
    python init_admin.py

首次运行前请确保 MySQL 服务已启动，并已执行 init_info_db.sql 创建数据库和表。
"""
import hashlib
from database_mysql import init_mysql, get_db


def _hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_default_admin():
    """创建默认超级管理员账号"""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id FROM admins WHERE username = 'admin'")
        if cursor.fetchone():
            print("[OK] 超级管理员账号 'admin' 已存在")
            return

        cursor.execute(
            "INSERT INTO admins (username, password_hash, display_name, role) VALUES (%s, %s, %s, %s)",
            ('admin', _hash_password('admin123'), '超级管理员', 'super_admin')
        )
    db.commit()
    print("[OK] 默认超级管理员账号创建成功")
    print("     用户名: admin")
    print("     密码:   admin123")
    print(" !!! 请尽快修改密码 !!!")


def main():
    print("=" * 50)
    print("实训评价系统 - MySQL 数据库初始化")
    print("=" * 50)

    print("\n[1/2] 验证数据库连接...")
    try:
        init_mysql()
        print("[OK] 已连接到「信息」库，teachers / admins 表就绪")
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        print("\n请检查:")
        print("  1. MySQL 服务是否已启动")
        print("  2. 是否已执行 init_info_db.sql 创建数据库和表")
        print("  3. config.py 中的 MYSQL_PASSWORD 是否为 123456")
        return

    print("\n[2/2] 创建默认超级管理员...")
    try:
        create_default_admin()
    except Exception as e:
        print(f"[ERROR] 创建管理员失败: {e}")
        return

    print("\n" + "=" * 50)
    print("初始化完成！现在可以启动系统：python main.py")
    print("=" * 50)


if __name__ == '__main__':
    main()
