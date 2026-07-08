import os
import sys
import json
import re
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

from database import init_db
from database_mysql import init_mysql
from config import UPLOAD_DIR, REPORT_DIR 
from routers import training, evaluation, report, llm, system_config, admin_tools, homework, courses, eval_config, growth, modify, recommend
from users_router import handle_login, handle_list_users, handle_create_user, handle_update_user, handle_delete_user

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

init_db()
init_mysql()

# 注意：RAG 引擎不再在启动时自动初始化/构建索引。
# 向量索引属于一次性操作，需通过 /api/modify/rebuild-index 手动触发重建。

class SafeHTTPServer(HTTPServer):
    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(self.server_address)
        except Exception:
            self.socket.bind((self.server_address[0], 0))
        self.server_name = 'localhost'
        self.server_port = self.socket.getsockname()[1]

class RequestHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-User-Id, X-User-Name, X-User-Role, X-User-Type, X-Account-Type, X-User-Display-Name')
        self.end_headers()

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_PUT(self):
        self.handle_request('PUT')

    def do_DELETE(self):
        self.handle_request('DELETE')

    def handle_request(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        try:
            if path.startswith('/uploads/'):
                self.serve_static(path[9:], UPLOAD_DIR)
                return
            if path.startswith('/reports/'):
                self.serve_static(path[9:], REPORT_DIR)
                return
            if path.startswith('/api/'):
                pass
            else:
                self.serve_frontend(path)
                return

            handler = self.route_request(method, path, query)
            if handler:
                status, headers, body = handler(method, path, query, self)
                self.send_response(status)
                for key, value in headers:
                    self.send_header(key, value)
                self.end_headers()
                if body:
                    self.wfile.write(body.encode('utf-8') if isinstance(body, str) else body)
            else:
                self.send_json(404, {'detail': 'Not Found'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            import sys as _sys
            _sys.stdout.flush()
            self.send_json(500, {'detail': repr(e)})

    def route_request(self, method, path, query):
        routes = [
            (r'^/api/health$', lambda m, p, q, h: self.handle_health()),
            (r'^/api/system/config$', lambda m, p, q, h: self.route_system_config(method)),
            (r'^/api/admin/class-stats$', lambda m, p, q, h: admin_tools.handle_class_stats(self)),
            (r'^/api/teacher/classes$', lambda m, p, q, h: admin_tools.handle_teacher_classes(self)),
            (r'^/api/teacher/classes/(\d+)/status$', lambda m, p, q, h: self.route_teaching_status(m, p)),
            (r'^/api/teacher/classes/(\d+)$', lambda m, p, q, h: self.route_teacher_class(m, p)),
            (r'^/api/admin/logs$', lambda m, p, q, h: admin_tools.handle_list_logs(self)),
            (r'^/api/admin/backup$', lambda m, p, q, h: admin_tools.handle_backup(self)),
            (r'^/api/evaluation/templates$', lambda m, p, q, h: self.route_template_collection(method)),
            (r'^/api/evaluation/templates/(\d+)/assign$', lambda m, p, q, h: self.route_template_assign(method, p)),
            (r'^/api/evaluation/templates/(\d+)/assignments$', lambda m, p, q, h: self.route_template_assignments(method, p)),
            (r'^/api/evaluation/templates/(\d+)$', lambda m, p, q, h: self.route_template_detail(method, p)),
            (r'^/api/training/list$', lambda m, p, q, h: training.handle_list_trainings(self)),
            (r'^/api/training/(\d+)$', lambda m, p, q, h: self.route_training(method, p)),
            (r'^/api/training/create$', lambda m, p, q, h: training.handle_create_training(self)),
            (r'^/api/training/(\d+)/document$', lambda m, p, q, h: training.handle_upload_training_document(self, p)),
            (r'^/api/training/(\d+)/submit$', lambda m, p, q, h: training.handle_submit_work(self, p)),
            (r'^/api/training/(\d+)/submissions$', lambda m, p, q, h: training.handle_list_submissions(self, p)),
            (r'^/api/training/submission/(\d+)$', lambda m, p, q, h: self.route_submission(method, p)),
            (r'^/api/training/(\d+)/eval-config$', lambda m, p, q, h: self.route_eval_config(method, p)),
            (r'^/api/evaluation/indicators/(\d+)$', lambda m, p, q, h: evaluation.handle_list_indicators(self, p)),
            (r'^/api/evaluation/indicators$', lambda m, p, q, h: evaluation.handle_create_indicator(self)),
            (r'^/api/evaluation/indicators/(\d+)$', lambda m, p, q, h: self.route_indicator(method, p)),
            (r'^/api/evaluation/evaluate/(\d+)$', lambda m, p, q, h: evaluation.handle_evaluate_submission(self, p)),
            (r'^/api/evaluation/batch-evaluate/(\d+)$', lambda m, p, q, h: evaluation.handle_batch_evaluate(self, p)),
            (r'^/api/evaluation/teacher-review/(\d+)$', lambda m, p, q, h: evaluation.handle_teacher_review(self, p)),
            (r'^/api/evaluation/reparse/(\d+)$', lambda m, p, q, h: evaluation.handle_reparse_submission(self, p)),
            (r'^/api/report/stats$', lambda m, p, q, h: report.handle_stats(self)),
            (r'^/api/report/training/(\d+)/data$', lambda m, p, q, h: report.handle_training_report_data(self, p)),
            (r'^/api/report/training/(\d+)/common-problems$', lambda m, p, q, h: report.handle_common_problems(self, p)),
            (r'^/api/report/training/(\d+)/abnormal-students$', lambda m, p, q, h: report.handle_abnormal_students(self, p)),
            (r'^/api/report/training/(\d+)/export-problems$', lambda m, p, q, h: report.handle_export_common_problems(self, p)),
            (r'^/api/report/training/(\d+)/follow-up$', lambda m, p, q, h: report.handle_add_follow_up(self, p)),
            (r'^/api/report/generate/(\d+)$', lambda m, p, q, h: report.handle_generate_report(self, p)),
            (r'^/api/report/generate/student/(\d+)$', lambda m, p, q, h: report.handle_generate_single_student_report(self, p)),
            (r'^/api/report/batch-generate/(\d+)$', lambda m, p, q, h: report.handle_batch_generate_reports(self, p)),
            (r'^/api/report/list/(\d+)$', lambda m, p, q, h: report.handle_list_reports(self, p)),
            (r'^/api/report/download/(\d+)/pdf$', lambda m, p, q, h: report.handle_download_pdf(self, p)),
            (r'^/api/report/download/(\d+)/excel$', lambda m, p, q, h: report.handle_download_excel(self, p)),
            (r'^/api/report/student/(\d+)$', lambda m, p, q, h: report.handle_student_report(self, p)),
            (r'^/api/report/classes$', lambda m, p, q, h: report.handle_training_classes(self, p)),
            (r'^/api/report/submissions$', lambda m, p, q, h: report.handle_list_submissions(self, p)),
            (r'^/api/report/submission/(\d+)/categories$', lambda m, p, q, h: report.handle_submission_categories(self, p)),
            (r'^/api/report/submission/(\d+)/detail$', lambda m, p, q, h: report.handle_category_detail(self, p)),
            (r'^/api/report/submission/(\d+)/category-review$', lambda m, p, q, h: report.handle_category_review(self, p)),
            (r'^/api/report/\d+$', lambda m, p, q, h: self.route_report(method, p)),
            (r'^/api/growth/analysis$', lambda m, p, q, h: growth.handle_growth_analysis(h)),
            (r'^/api/auth/login$', lambda m, p, q, h: handle_login(h)),
            (r'^/api/users$', lambda m, p, q, h: self.route_users(method, h)),
            (r'^/api/users/(\d+)$', lambda m, p, q, h: self.route_user_detail(method, h, p)),
            (r'^/api/llm/config$', lambda m, p, q, h: self.route_llm_config(method)),
            (r'^/api/llm/test$', lambda m, p, q, h: llm.handle_test_llm_connection(self)),
            # 作业提交模块
            (r'^/api/homework/upload$', lambda m, p, q, h: homework.handle_homework_upload(self)),
            (r'^/api/homework/teacher/submissions$', lambda m, p, q, h: homework.handle_teacher_submissions(self)),
            (r'^/api/homework/teacher/class-list$', lambda m, p, q, h: homework.handle_teacher_class_list(self)),
            (r'^/api/homework/teacher/trainings$', lambda m, p, q, h: homework.handle_teacher_training_list(self)),
            (r'^/api/homework/review/(\d+)$', lambda m, p, q, h: homework.handle_teacher_review(self, p)),
            (r'^/api/homework/file/(\d+)$', lambda m, p, q, h: homework.handle_serve_homework_file(self, p)),
            # 课程模块
            (r'^/api/courses/student/mine$', lambda m, p, q, h: courses.handle_student_courses(self)),
            (r'^/api/courses/student/mine/trainings$', lambda m, p, q, h: courses.handle_student_all_trainings(self)),
            (r'^/api/courses/student/(\d+)/trainings$', lambda m, p, q, h: courses.handle_student_course_trainings(self, re.search(r'/student/(\d+)/trainings', p).group(1))),
            (r'^/api/courses/teacher/mine$', lambda m, p, q, h: courses.handle_teacher_courses(self)),
            (r'^/api/courses/teacher/mine/trainings$', lambda m, p, q, h: courses.handle_teacher_all_trainings(self)),
            (r'^/api/courses/teacher/(\d+)/classes$', lambda m, p, q, h: courses.handle_teacher_course_classes(self, re.search(r'/(\d+)/classes', p).group(1))),
            (r'^/api/courses/teacher/classes/(\d+)/students$', lambda m, p, q, h: courses.handle_teacher_class_students(self, re.search(r'/classes/(\d+)/students', p).group(1))),
            (r'^/api/semesters/current$', lambda m, p, q, h: courses.handle_current_semester(self)),
            # 学生项目与提交
            (r'^/api/training/my-projects$', lambda m, p, q, h: training.handle_student_my_projects(self)),
            (r'^/api/training/my-submissions$', lambda m, p, q, h: training.handle_student_my_submissions(self)),
            # 学生提交记录
            (r'^/api/submissions/student/mine$', lambda m, p, q, h: training.handle_student_submissions(self)),
            # 作业修改模块（RAG + LLM）
            (r'^/api/modify/submission$', lambda m, p, q, h: modify.handle_modify_submission(self)),
            (r'^/api/modify/specs$', lambda m, p, q, h: modify.handle_get_specs(self)),
            (r'^/api/modify/categories$', lambda m, p, q, h: modify.handle_get_categories(self)),
            (r'^/api/modify/rebuild-index$', lambda m, p, q, h: modify.handle_rebuild_index(self)),
            # 知识图谱与课程推荐
            (r'^/api/knowledge/graph$', lambda m, p, q, h: recommend.handle_get_graph(self)),
            (r'^/api/knowledge/points$', lambda m, p, q, h: recommend.handle_get_points(self)),
            (r'^/api/knowledge/prerequisites$', lambda m, p, q, h: recommend.handle_get_prerequisites(self)),
            (r'^/api/knowledge/analyze$', lambda m, p, q, h: recommend.handle_analyze_weakness(self)),
            (r'^/api/recommend/courses$', lambda m, p, q, h: recommend.handle_recommend_courses(self)),
            (r'^/api/recommend/analyze-and-recommend$', lambda m, p, q, h: recommend.handle_analyze_and_recommend(self)),
        ]

        for pattern, handler in routes:
            match = re.match(pattern, path)
            if match:
                return handler
        return None

    def route_training(self, method, path):
        training_id = int(re.search(r'/api/training/(\d+)', path).group(1))
        if method == 'GET':
            return training.handle_get_training(self, training_id)
        elif method == 'PUT':
            return training.handle_update_training(self, training_id)
        elif method == 'DELETE':
            return training.handle_delete_training(self, training_id)

    def route_submission(self, method, path):
        submission_id = int(re.search(r'/api/training/submission/(\d+)', path).group(1))
        if method == 'GET':
            return training.handle_get_submission(self, submission_id)
        elif method == 'DELETE':
            return training.handle_delete_submission(self, submission_id)

    def route_eval_config(self, method, path):
        training_id = int(re.search(r'/api/training/(\d+)', path).group(1))
        if method == 'GET':
            return eval_config.handle_get_eval_config(self, path)
        elif method == 'PUT':
            return eval_config.handle_update_eval_config(self, path)
        return 405, [('Content-Type', 'application/json')], json.dumps({'detail': '方法不允许'}, ensure_ascii=False)

    def route_indicator(self, method, path):
        indicator_id = int(re.search(r'/api/evaluation/indicators/(\d+)', path).group(1))
        if method == 'PUT':
            return evaluation.handle_update_indicator(self, indicator_id)
        elif method == 'DELETE':
            return evaluation.handle_delete_indicator(self, indicator_id)

    def route_report(self, method, path):
        report_id = int(re.search(r'/api/report/(\d+)', path).group(1))
        if method == 'DELETE':
            return report.handle_delete_report(self, report_id)

    def route_template_collection(self, method):
        if method == 'GET':
            return evaluation.handle_list_templates(self)
        elif method == 'POST':
            return evaluation.handle_create_template(self)

    def route_template_detail(self, method, path):
        template_id = int(re.search(r'/api/evaluation/templates/(\d+)', path).group(1))
        if method == 'GET':
            return evaluation.handle_get_template(self, template_id)
        elif method == 'PUT':
            return evaluation.handle_update_template(self, template_id)
        elif method == 'DELETE':
            return evaluation.handle_delete_template(self, template_id)

    def route_template_assign(self, method, path):
        template_id = int(re.search(r'/api/evaluation/templates/(\d+)', path).group(1))
        if method == 'POST':
            return evaluation.handle_assign_template(self, template_id)
        return 405, [('Content-Type', 'application/json')], json.dumps({'detail': '方法不允许'}, ensure_ascii=False)

    def route_template_assignments(self, method, path):
        template_id = int(re.search(r'/api/evaluation/templates/(\d+)', path).group(1))
        if method == 'GET':
            return evaluation.handle_get_template_assignments(self, template_id)
        return 405, [('Content-Type', 'application/json')], json.dumps({'detail': '方法不允许'}, ensure_ascii=False)

    def route_llm_config(self, method):
        if method == 'GET':
            return llm.handle_get_llm_config(self)
        elif method == 'PUT':
            return llm.handle_update_llm_config(self)

    def route_system_config(self, method):
        if method == 'GET':
            return system_config.handle_get_system_config()
        elif method == 'PUT':
            return system_config.handle_update_system_config(self)

    def route_users(self, method, handler):
        if method == 'GET':
            return handle_list_users(handler)
        elif method == 'POST':
            return handle_create_user(handler)

    def route_user_detail(self, method, handler, path):
        import re
        user_id = int(re.search(r'/api/users/(\d+)', path).group(1))
        if method == 'PUT':
            return handle_update_user(handler, user_id)
        elif method == 'DELETE':
            return handle_delete_user(handler, user_id)

    def route_teaching_status(self, method, path):
        import re
        class_id = int(re.search(r'/api/teacher/classes/(\d+)', path).group(1))
        if method == 'PUT':
            return admin_tools.handle_update_teaching_status(self, class_id)
        return 405, [('Content-Type', 'application/json')], json.dumps({'detail': '方法不允许'}, ensure_ascii=False)

    def route_teacher_class(self, method, path):
        import re
        class_id = int(re.search(r'/api/teacher/classes/(\d+)', path).group(1))
        if method == 'GET':
            return admin_tools.handle_get_teacher_class(self, class_id)
        return 405, [('Content-Type', 'application/json')], json.dumps({'detail': '方法不允许'}, ensure_ascii=False)

    def handle_health(self):
        return 200, [('Content-Type', 'application/json')], json.dumps({'status': 'ok', 'service': '实训评价系统'})

    def serve_static(self, filepath, base_dir):
        full_path = os.path.join(base_dir, filepath)
        if not os.path.exists(full_path) or not full_path.startswith(base_dir):
            self.send_json(404, {'detail': 'File not found'})
            return
        ext = os.path.splitext(filepath)[1].lower()
        mime = {
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.html': 'text/html',
            '.txt': 'text/plain',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }.get(ext, 'application/octet-stream')
        with open(full_path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Disposition', f'inline; filename="{os.path.basename(full_path)}"')
        self.end_headers()
        self.wfile.write(content)

    def serve_frontend(self, path):
        if path == '/':
            filepath = 'login.html'
        elif path == '/index.html':
            filepath = 'index.html'
        else:
            filepath = path.lstrip('/')
        filepath = unquote(filepath)
        full_path = os.path.join(FRONTEND_DIR, filepath)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            ext = os.path.splitext(filepath)[1].lower()
            mime = {
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
            }.get(ext, 'text/plain')
            with open(full_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', f'{mime}; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        else:
            with open(os.path.join(FRONTEND_DIR, 'index.html'), 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(content_length) if content_length > 0 else b''

    def parse_json_body(self):
        body = self.read_body()
        if not body:
            return {}
        try:
            return json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            return {}

    parse_body_json = parse_json_body

    def parse_form_body(self):
        content_type = self.headers.get('Content-Type', '')
        body = self.read_body()
        if content_type.startswith('multipart/form-data'):
            boundary = content_type.split('boundary=')[1].encode('utf-8')
            parts = body.split(b'--' + boundary)
            data = {}
            files = {}
            for part in parts[1:-1]:
                lines = part.strip(b'\r\n').split(b'\r\n')
                headers = {}
                i = 0
                while i < len(lines) and lines[i]:
                    if b':' in lines[i]:
                        key, value = lines[i].split(b':', 1)
                        headers[key.strip().decode('utf-8')] = value.strip().decode('utf-8')
                    i += 1
                content = b'\r\n'.join(lines[i+1:]).strip()
                content_disposition = headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    fname = content_disposition.split('filename=')[1].strip('"')
                    files[fname] = content
                else:
                    name = content_disposition.split('name=')[1].strip('"')
                    data[name] = content.decode('utf-8') if content else ''
            return data, files
        elif content_type.startswith('application/x-www-form-urlencoded'):
            return parse_qs(body.decode('utf-8')), {}
        return {}, {}

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

def run_server(host='127.0.0.1', port=8000):
    server = SafeHTTPServer((host, port), RequestHandler)
    actual_port = server.server_port
    print(f"Server running on http://{host}:{actual_port}")
    print(f"API docs: http://{host}:{actual_port}/api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopping...")
        server.server_close()

if __name__ == "__main__":
    run_server()