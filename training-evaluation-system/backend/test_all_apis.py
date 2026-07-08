# -*- coding: utf-8 -*-
"""验证全部关键 API"""
import sys, os, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

def test(path, headers=None, method='GET', body=None):
    hdrs = {'X-User-Id': '1'}
    if headers: hdrs.update(headers)
    data = body.encode() if body else None
    req = urllib.request.Request(f'http://127.0.0.1:8000{path}', data=data, headers=hdrs, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        ctype = resp.headers.get('Content-Type', '')
        if 'json' in ctype:
            return resp.status, json.loads(resp.read().decode())
        return resp.status, resp.read()[:500]
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except:
            return e.code, str(e)

print('=== 健康检查 ===')
s, d = test('/api/health')
print(f'  {s}: {d}')

print('\n=== 作业教师班级列表 ===')
s, d = test('/api/homework/teacher/class-list')
print(f'  {s}: {json.dumps(d, ensure_ascii=False)[:200]}')

print('\n=== 作业教师提交列表 ===')
s, d = test('/api/homework/teacher/submissions?class_id=1&training_id=1')
print(f'  {s}: {json.dumps(d, ensure_ascii=False)[:200]}')

print('\n=== 实训列表 ===')
s, d = test('/api/training/list')
print(f'  {s}: total={d.get("total")}')

print('\n=== 教师课程 ===')
s, d = test('/api/courses/teacher/mine')
print(f'  {s}: {d.get("total")} 门课程')

print('\n=== 学生课程 ===')
s, d = test('/api/courses/student/mine')
print(f'  {s}: {d.get("total")} 门课程')

print('\n=== 教师课程班级列表(ID=1) ===')
s, d = test('/api/courses/teacher/1/classes')
print(f'  {s}: {d.get("total")} 个班级')

print('\n全部 API 验证完成 ✅')
