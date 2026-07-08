# -*- coding: utf-8 -*-
import sys, io, json, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/homework/teacher/submissions',
    headers={'X-User-Id': '1'},
    method='GET'
)
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        print("200:", resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"{e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
