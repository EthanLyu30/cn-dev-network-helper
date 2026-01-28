import http.server
import socketserver
import json
import webbrowser
import os
import sys
from functools import partial
from ..core.utils import detect_proxy_port
from ..modules.python import set_pip_mirror, set_pip_proxy, set_conda_mirror, set_conda_proxy
from ..modules.node import set_node_mirror, set_node_proxy
from ..modules.git import set_git_proxy
from ..modules.go import set_go_proxy
from ..modules.docker import set_docker_mirror

PORT = 8000
WEB_ROOT = os.path.join(os.path.dirname(__file__), 'static')

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def do_POST(self):
        if self.path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                response = self.handle_api(self.path, data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_error(404)

    def handle_api(self, path, data):
        action = path.split('/')[-1]
        
        if action == 'detect_port':
            port = detect_proxy_port()
            return {'status': 'success', 'port': port}
            
        elif action == 'apply_config':
            module = data.get('module')
            mode = data.get('mode') # mirror or proxy
            port = data.get('port')
            
            if module == 'python':
                if mode == 'mirror':
                    set_pip_mirror()
                    set_conda_mirror()
                elif mode == 'proxy':
                    set_pip_proxy(port)
                    set_conda_proxy(port)
                    
            elif module == 'node':
                if mode == 'mirror':
                    set_node_mirror()
                elif mode == 'proxy':
                    set_node_proxy(port)
            
            elif module == 'git':
                if mode == 'proxy': # Git only has smart proxy mode here
                    set_git_proxy(port)
            
            elif module == 'go':
                if mode == 'mirror': # Go uses proxy as mirror effectively
                    set_go_proxy()
            
            elif module == 'docker':
                if mode == 'mirror':
                    set_docker_mirror()
            
            return {'status': 'success', 'message': f'{module} 配置已应用 ({mode})'}
            
        return {'status': 'error', 'message': 'Unknown action'}

    def log_message(self, format, *args):
        pass # Suppress logging

def launch_web_ui():
    Handler = RequestHandler
    print(f"正在启动 Web 界面: http://localhost:{PORT}")
    print("请在浏览器中查看...")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{PORT}")
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nWeb 服务已停止")
