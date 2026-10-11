import http.server
import urllib.request
import json
import os

PORT = int(os.environ.get('PORT', 8080))

class Proxy(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        target = self.headers.get('X-Target-URL')
        auth = self.headers.get('X-Auth', '')

        if not target:
            self.send_response(400)
            self._cors()
            self.end_headers()
            self.wfile.write(b'{"error":"no target"}')
            return

        req = urllib.request.Request(target, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        if auth:
            req.add_header('Authorization', auth)
        req.add_header('x-api-key', auth.replace('Bearer ', '') if auth.startswith('Bearer') else auth)
        req.add_header('anthropic-version', '2023-06-01')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        req.add_header('Accept', 'application/json')

        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                self.send_response(r.status)
                self._cors()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, *args):
        pass

print(f'Proxy running on port {PORT}')
http.server.HTTPServer(('0.0.0.0', PORT), Proxy).serve_forever()
