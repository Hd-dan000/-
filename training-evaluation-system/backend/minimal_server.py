# -*- coding: utf-8 -*-
"""Direct server test - capture full server-side traceback"""
import sys, io, os, json, traceback, re, socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from database_mysql import init_mysql
from config import UPLOAD_DIR, REPORT_DIR
from routers import training, evaluation, report, llm, system_config, admin_tools, homework
from users_router import handle_login, handle_list_users, handle_create_user, handle_update_user, handle_delete_user

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

init_db()
init_mysql()

class SaferServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(self.server_address)
        except Exception:
            self.socket.bind((self.server_address[0], 0))
        self.server_name = 'localhost'
        self.server_port = self.socket.getsockname()[1]

class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self): self.handle_request('GET')
    def do_POST(self): self.handle_request('POST')
    def do_PUT(self): self.handle_request('PUT')
    def do_DELETE(self): self.handle_request('DELETE')

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def read_body(self):
        cl = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(cl) if cl > 0 else b''

    def parse_json_body(self):
        body = self.read_body()
        if not body: return {}
        try: return json.loads(body.decode('utf-8'))
        except: return {}

    def parse_form_body(self):
        ct = self.headers.get('Content-Type', '')
        body = self.read_body()
        if ct.startswith('multipart/form-data'):
            boundary = ct.split('boundary=')[1].encode('utf-8')
            parts = body.split(b'--' + boundary)
            data = {}; files = {}
            for part in parts[1:-1]:
                lines = part.split(b'\r\n')
                hdrs = {}
                i = 0
                while i < len(lines) and lines[i]:
                    if b':' in lines[i]:
                        k, v = lines[i].split(b':', 1)
                        hdrs[k.strip().decode('utf-8')] = v.strip().decode('utf-8')
                    i += 1
                content = b'\r\n'.join(lines[i+1:]).strip()
                cd = hdrs.get('Content-Disposition', '')
                if 'filename=' in cd:
                    fn = cd.split('filename=')[1].strip('"')
                    files[fn] = content
                else:
                    name = cd.split('name=')[1].strip('"')
                    data[name] = content.decode('utf-8') if content else ''
            return data, files
        return {}, {}

    def handle_request(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            if path.startswith('/uploads/'):
                self.serve_static(path[9:], UPLOAD_DIR); return
            if path.startswith('/reports/'):
                self.serve_static(path[9:], REPORT_DIR); return
            if not path.startswith('/api/'):
                self.serve_frontend(path); return

            handler = self.route_request(method, path, query)
            if handler:
                status, headers, body = handler(method, path, query, self)
                self.send_response(status)
                for k, v in headers:
                    self.send_header(k, v)
                self.end_headers()
                if body:
                    self.wfile.write(body.encode('utf-8') if isinstance(body, str) else body)
            else:
                self.send_json(404, {'detail': 'Not Found'})
        except Exception as e:
            traceback.print_exc()
            import sys as _sys
            _sys.stdout.flush()
            err_str = traceback.format_exc()
            with open('server_error.log', 'w', encoding='utf-8') as ef:
                ef.write(err_str)
            self.send_json(500, {'detail': repr(e) + ' | ' + str(e)})

    def route_request(self, method, path, query):
        routes = [
            (r'^/api/health$', lambda m, p, q, h: self.handle_health()),
            (r'^/api/homework/teacher/submissions$', lambda m, p, q, h: homework.handle_teacher_submissions(h)),
            (r'^/api/homework/teacher/class-list$', lambda m, p, q, h: homework.handle_teacher_class_list(h)),
        ]
        for pattern, func in routes:
            if re.match(pattern, path):
                return func
        return None

    def handle_health(self):
        return 200, [('Content-Type', 'application/json')], json.dumps({'status': 'ok'})

    def log_message(self, format, *args):
        pass

server = SaferServer(('127.0.0.1', 8000), Handler)
print(f"Server on http://127.0.0.1:{server.server_port}")
server.serve_forever()
