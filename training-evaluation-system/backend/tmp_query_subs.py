import sqlite3
conn = sqlite3.connect('data.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
print('=== submissions by training/class/status ===')
c.execute('SELECT training_id, class_id, status, COUNT(*) as cnt FROM submissions GROUP BY training_id, class_id, status')
for row in c.fetchall():
    print(dict(row))
print('=== evaluated samples ===')
c.execute("SELECT id, training_id, class_id, student_id, student_name, status, final_score FROM submissions WHERE status='evaluated' LIMIT 10")
for row in c.fetchall():
    print(dict(row))
