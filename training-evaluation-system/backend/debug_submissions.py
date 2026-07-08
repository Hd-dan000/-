# -*- coding: utf-8 -*-
"""Debug: simulate submissions endpoint"""
import sys, io, os, json, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from routers.homework import handle_teacher_submissions

class FakeHandler:
    path = '/api/homework/teacher/submissions'
    headers = {'X-User-Id': '1'}

try:
    result = handle_teacher_submissions(FakeHandler())
    print(f"Status: {result[0]}")
    print(f"Headers: {result[1]}")
    body = result[2]
    if isinstance(body, bytes):
        body = body.decode('utf-8')
    print(f"Body: {body[:500]}")
except Exception as e:
    traceback.print_exc()
