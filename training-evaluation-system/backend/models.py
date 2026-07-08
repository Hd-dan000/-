CREATE_TABLES = {
    'trainings': '''
        CREATE TABLE IF NOT EXISTS trainings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            course_name TEXT,
            teacher_name TEXT,
            expected_steps TEXT,
            expected_outcomes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'submissions': '''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            student_id TEXT,
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''',
    'evaluation_indicators': '''
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
    ''',
    'evaluation_reports': '''
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
    ''',
    'system_config': '''
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'follow_up_records': '''
        CREATE TABLE IF NOT EXISTS follow_up_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            training_id INTEGER NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    '''
}