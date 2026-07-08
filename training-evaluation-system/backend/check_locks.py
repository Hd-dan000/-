# -*- coding: utf-8 -*-
"""检查 MySQL 进程和锁"""
import sys, os, pymysql
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

conn = pymysql.connect(host='127.0.0.1', user='root', password='123456', charset='utf8mb4', connect_timeout=5)
my_id = conn.thread_id()

with conn.cursor() as c:
    c.execute('SHOW PROCESSLIST')
    print('=== PROCESSLIST ===')
    for r in c.fetchall():
        tid, user, host, db, cmd, _, state, info = r
        if tid == my_id:
            print(f'  {tid:>5d}  ← 本连接')
        else:
            print(f'  {tid:>5d}  user={user}  db={db}  cmd={cmd:8s}  state={state}')

    # 查元数据锁
    c.execute("SELECT * FROM information_schema.INNODB_TRX")
    print('\n=== INNODB_TRX ===')
    for r in c.fetchall():
        print(f'  {r}')

print('Done, my_id:', my_id)
conn.close()
