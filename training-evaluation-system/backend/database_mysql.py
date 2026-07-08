"""MySQL 数据库模块 - 连接「信息」库中的 teachers / admins 表"""
import pymysql
import pymysql.cursors
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

_conn = None


def get_db():
    global _conn
    if _conn is None or not _conn.open:
        _conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    return _conn


def dict_from_row(row):
    return row


def init_mysql():
    """验证 MySQL 连接，并确认 teachers / admins / students 表已存在"""
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
                (MYSQL_DATABASE,),
            )
            if not cursor.fetchone():
                raise RuntimeError(
                    f"数据库 `{MYSQL_DATABASE}` 不存在，请先执行 init_info_db.sql 创建数据库和表"
                )
    finally:
        conn.close()

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE 'teachers'")
        if not cursor.fetchone():
            raise RuntimeError("表 `teachers` 不存在，请先执行 init_info_db.sql")
        cursor.execute("SHOW TABLES LIKE 'admins'")
        if not cursor.fetchone():
            raise RuntimeError("表 `admins` 不存在，请先执行 init_info_db.sql")
        cursor.execute("SHOW TABLES LIKE 'students'")
        if not cursor.fetchone():
            raise RuntimeError("表 `students` 不存在，请先执行 init_info_db.sql")
        cursor.execute("SHOW TABLES LIKE 'classes'")
        if cursor.fetchone():
            cursor.execute("SHOW COLUMNS FROM `classes` LIKE 'teaching_status'")
            if not cursor.fetchone():
                cursor.execute(
                    "ALTER TABLE `classes` ADD COLUMN `teaching_status` VARCHAR(20) DEFAULT 'not_started' "
                    "COMMENT '开课状态:not_started未开课/in_progress开课中/ended已结课' "
                    "AFTER `create_teacher_id`"
                )
                db.commit()
                print("[migrate] 已添加 classes.teaching_status 字段")
