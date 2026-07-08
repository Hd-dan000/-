# -*- coding: utf-8 -*-
"""测试课程 API"""
import sys, os, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

def test(path, headers=None):
    hdrs = {'X-User-Id': '1'}
    if headers: hdrs.update(headers)
    req = urllib.request.Request(f'http://127.0.0.1:8000{path}', headers=hdrs)
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return None, str(e)

print('=== 教师课程 ===')
s, d = test('/api/courses/teacher/mine')
print(f'{s}: total={d.get("total")}')
for c in d.get('courses', []):
    print(f'  [{c["course_code"]}] {c["course_name"]} ({c["class_count"]}个班级)')

print()
print('=== 教师课程班级(课程ID=1) ===')
s, d = test('/api/courses/teacher/1/classes')
print(f'{s}: {json.dumps(d, ensure_ascii=False)[:300]}')

print()
print('=== 学生课程 ===')
s, d = test('/api/courses/student/mine')
print(f'{s}: total={d.get("total")}')
for c in d.get('courses', []):
    print(f'  [{c["course_code"]}] {c["course_name"]}')
