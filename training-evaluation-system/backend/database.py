import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH

_db_conns = {}

def get_db():
    if DATABASE_PATH not in _db_conns:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _db_conns[DATABASE_PATH] = conn
    return _db_conns[DATABASE_PATH]

def dict_from_row(row):
    if row is None:
        return None
    return dict(row)

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trainings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            course_name TEXT,
            teacher_name TEXT,
            expected_steps TEXT,
            expected_outcomes TEXT,
            course_id INTEGER DEFAULT 0,
            deadline TEXT,
            dimensions TEXT DEFAULT '[]',
            document_url TEXT,
            code_standard TEXT,
            category_weights TEXT DEFAULT '{"document":0.333,"ui":0.333,"code":0.333}',
            status TEXT DEFAULT 'not_started',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 兼容已有数据库：确保 trainings 表存在所需列
    cursor.execute("PRAGMA table_info(trainings)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    migrations = [
        ('course_id', 'ALTER TABLE trainings ADD COLUMN course_id INTEGER DEFAULT 0'),
        ('deadline', 'ALTER TABLE trainings ADD COLUMN deadline TEXT'),
        ('dimensions', "ALTER TABLE trainings ADD COLUMN dimensions TEXT DEFAULT '[]'"),
        ('document_url', 'ALTER TABLE trainings ADD COLUMN document_url TEXT'),
        ('code_standard', 'ALTER TABLE trainings ADD COLUMN code_standard TEXT'),
        ('category_weights', 'ALTER TABLE trainings ADD COLUMN category_weights TEXT DEFAULT \'{"document":0.333,"ui":0.333,"code":0.333}\' '),
    ]
    for col, sql in migrations:
        if col not in existing_columns:
            cursor.execute(sql)

    # 实训与班级绑定关系表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL,
            class_id INTEGER NOT NULL,
            class_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(training_id, class_id),
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            student_id TEXT,
            class_id INTEGER,
            class_name TEXT,
            files TEXT DEFAULT '[]',
            parsed_content TEXT,
            step_completeness REAL,
            outcome_quality REAL,
            logic_score REAL,
            ai_total_score REAL,
            teacher_score REAL,
            teacher_comment TEXT,
            final_score REAL,
            evaluation_detail TEXT,
            status TEXT DEFAULT 'submitted',
            follow_note TEXT,
            category_teacher_scores TEXT DEFAULT '{}',
            category_teacher_comments TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''')

    # 兼容已有数据库：确保 submissions 表存在所需列
    cursor.execute("PRAGMA table_info(submissions)")
    existing_submission_columns = [row[1] for row in cursor.fetchall()]
    submission_migrations = [
        ('follow_note', 'ALTER TABLE submissions ADD COLUMN follow_note TEXT'),
        ('class_id', 'ALTER TABLE submissions ADD COLUMN class_id INTEGER'),
        ('class_name', 'ALTER TABLE submissions ADD COLUMN class_name TEXT'),
        ('category_teacher_scores', "ALTER TABLE submissions ADD COLUMN category_teacher_scores TEXT DEFAULT '{}'"),
        ('category_teacher_comments', "ALTER TABLE submissions ADD COLUMN category_teacher_comments TEXT DEFAULT '{}'"),
    ]
    for col, sql in submission_migrations:
        if col not in existing_submission_columns:
            cursor.execute(sql)

    # 跟进备注记录表（用于学生成长档案追溯）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS follow_up_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            training_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''')

    # 提交修订历史（教师复核记录，用于学生成长档案追溯）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submission_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL,
            score REAL,
            comment TEXT,
            changes TEXT DEFAULT '{}',
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            weight REAL DEFAULT 1.0,
            max_score REAL DEFAULT 100.0,
            indicator_type TEXT DEFAULT 'auto',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            indicators_json TEXT NOT NULL DEFAULT '[]',
            comment_templates_json TEXT DEFAULT '[]',
            error_rules_json TEXT DEFAULT '[]',
            alert_thresholds_json TEXT DEFAULT '{}',
            privacy_config_json TEXT DEFAULT '{}',
            is_default INTEGER DEFAULT 0,
            created_by TEXT,
            created_by_role TEXT DEFAULT 'teacher',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL,
            submission_id INTEGER,
            report_type TEXT,
            title TEXT,
            content_json TEXT,
            pdf_path TEXT,
            excel_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE,
            FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            operator TEXT,
            detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_evaluation_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL UNIQUE,
            comment_templates_json TEXT DEFAULT '[]',
            error_rules_json TEXT DEFAULT '[]',
            alert_thresholds_json TEXT DEFAULT '{}',
            privacy_config_json TEXT DEFAULT '{}',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_template_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL,
            template_id INTEGER NOT NULL,
            assigned_by TEXT,
            assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(training_id, template_id),
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE,
            FOREIGN KEY (template_id) REFERENCES evaluation_templates(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute("PRAGMA table_info(evaluation_templates)")
    template_columns = [row[1] for row in cursor.fetchall()]
    template_migrations = [
        ('comment_templates_json', "ALTER TABLE evaluation_templates ADD COLUMN comment_templates_json TEXT DEFAULT '[]'"),
        ('error_rules_json', "ALTER TABLE evaluation_templates ADD COLUMN error_rules_json TEXT DEFAULT '[]'"),
        ('alert_thresholds_json', "ALTER TABLE evaluation_templates ADD COLUMN alert_thresholds_json TEXT DEFAULT '{}'"),
        ('privacy_config_json', "ALTER TABLE evaluation_templates ADD COLUMN privacy_config_json TEXT DEFAULT '{}'"),
        ('created_by', 'ALTER TABLE evaluation_templates ADD COLUMN created_by TEXT'),
        ('created_by_role', "ALTER TABLE evaluation_templates ADD COLUMN created_by_role TEXT DEFAULT 'teacher'"),
    ]
    for col, sql in template_migrations:
        if col not in template_columns:
            cursor.execute(sql)

    conn.commit()
def now_str():
    return datetime.now().isoformat()
