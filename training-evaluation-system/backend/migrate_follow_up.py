import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'training_evaluation.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE submissions ADD COLUMN follow_note TEXT')
    print('Added follow_note column to submissions table')
except sqlite3.OperationalError:
    print('follow_note column already exists')

try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS follow_up_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            training_id INTEGER NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (training_id) REFERENCES trainings(id) ON DELETE CASCADE
        )
    ''')
    print('Created follow_up_records table')
except sqlite3.OperationalError:
    print('follow_up_records table already exists')

conn.commit()
conn.close()
print('Migration completed successfully')