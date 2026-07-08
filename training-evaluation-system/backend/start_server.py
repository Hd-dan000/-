# -*- coding: utf-8 -*-
import sys, io, os, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from http.server import HTTPServer, BaseHTTPRequestHandler
import main

class DebugHandler(main.RequestHandler):
    def handle_request(self, method):
        try:
            super().handle_request(method)
        except Exception:
            import traceback
            err = traceback.format_exc()
            print(f"ERROR: {err}", file=sys.stderr)
            # Write to file too
            with open('server_error.log', 'a', encoding='utf-8') as f:
                f.write(f"ERROR [{method} {self.path}]:\n{err}\n\n")
            self.send_json(500, {'detail': str(err[-300:])})

server = main.SafeHTTPServer(('127.0.0.1', 8000), DebugHandler)
print(f"服务器启动成功！ http://127.0.0.1:{server.server_port}")
server.serve_forever()
