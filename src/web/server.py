import http.server
import socketserver
import json
import webbrowser
import os
import sys
import threading
import time
import uuid
import queue
import urllib.parse
import io
import contextlib
import re
import ctypes
from ..core.utils import detect_proxy_port
from ..modules.python import set_pip_mirror, set_pip_proxy, set_conda_mirror, set_conda_proxy
from ..modules.node import set_node_mirror, set_node_proxy
from ..modules.git import set_git_proxy
from ..modules.go import set_go_proxy
from ..modules.docker import set_docker_mirror
from ..modules.hosts import update_github_hosts
from ..modules.proxy_tools import generate_terminal_proxy_commands, generate_lan_proxy_guide
from ..modules.templates import list_templates, apply_template
from ..modules.plugins import list_plugins, run_plugin
from ..modules.updater import check_for_updates
from ..modules.env_manager import analyze_project_path, create_venv_and_install, create_conda_and_install, quick_install_pkg, install_suite, get_system_info, get_all_suites

PORT = 8000
WEB_ROOT = os.path.join(os.path.dirname(__file__), 'static')
APP_VERSION = os.environ.get("APP_VERSION") or "4.0.0"
UPDATE_INFO = None

JOBS = {}
JOBS_LOCK = threading.Lock()
ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

def _is_admin():
    if not sys.platform.startswith("win"):
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def _relaunch_web_as_admin():
    if not sys.platform.startswith("win"):
        return False
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    main_py = os.path.join(repo_root, "main.py")
    params = f"\"{main_py}\" --web"
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, repo_root, 1)
        return int(rc) > 32
    except Exception:
        return False

def _now_ms():
    return int(time.time() * 1000)

def _refresh_update_info():
    global UPDATE_INFO
    try:
        UPDATE_INFO = check_for_updates(APP_VERSION, timeout=2)
    except Exception:
        UPDATE_INFO = None

def _new_job(action, params):
    job_id = uuid.uuid4().hex
    job = {
        'id': job_id,
        'action': action,
        'params': params,
        'status': 'running',
        'progress': 0,
        'created_at_ms': _now_ms(),
        'updated_at_ms': _now_ms(),
        'result': None,
        'error': None,
        'logs': [],
        'events': queue.Queue(),
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    return job

def _push_event(job, event):
    job['updated_at_ms'] = _now_ms()
    try:
        job['events'].put_nowait(event)
    except Exception:
        pass

def _log(job, level, message):
    entry = {'ts_ms': _now_ms(), 'level': level, 'message': message}
    job['logs'].append(entry)
    _push_event(job, {'type': 'log', **entry})

def _set_progress(job, value, title=None):
    job['progress'] = max(0, min(100, int(value)))
    payload = {'type': 'progress', 'value': job['progress']}
    if title:
        payload['title'] = title
    _push_event(job, payload)

def _strip_ansi(s):
    return ANSI_RE.sub('', s)

def _capture_stdout(fn, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ret = fn(*args, **kwargs)
    return ret, buf.getvalue()

def _log_captured_output(job, output):
    if not output:
        return
    cleaned = _strip_ansi(output)
    for line in cleaned.splitlines():
        line = line.strip()
        if line:
            _log(job, 'info', line)

def _finish_job(job, result):
    job['status'] = 'done'
    job['result'] = result
    _set_progress(job, 100)
    _push_event(job, {'type': 'done', 'result': result})

def _fail_job(job, error_message):
    job['status'] = 'error'
    job['error'] = error_message
    _push_event(job, {'type': 'error', 'error': error_message})

def _run_job(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return

    action = job['action']
    params = job['params'] or {}
    try:
        _set_progress(job, 5, '开始')
        if action == 'detect_port':
            _log(job, 'info', '正在检测代理端口')
            _set_progress(job, 30, '检测端口')
            port = detect_proxy_port()
            _log(job, 'info', f'检测到端口: {port}')
            _finish_job(job, {'port': port})
            return

        if action == 'update_hosts':
            _log(job, 'info', '准备更新 GitHub Hosts')
            _set_progress(job, 20, '拉取远端 Hosts')
            ok, output = _capture_stdout(update_github_hosts)
            _log_captured_output(job, output)
            _set_progress(job, 80, '写入 Hosts')
            if not ok:
                hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if sys.platform.startswith("win") else "/etc/hosts"
                if "Permission denied" in (output or "") or "没有权限写入 Hosts 文件" in (output or "") or "需要管理员权限" in (output or ""):
                    if sys.platform.startswith("win"):
                        tip = (
                            "更新 Hosts 失败：当前 Web 服务不是管理员权限，无法写入系统 Hosts。\n"
                            f"目标文件：{hosts_path}\n"
                            "解决方法：用管理员权限重新启动 Web 服务后再点一次。\n"
                            "在 Windows Terminal(管理员) 执行：\n"
                            "  cd d:\\git_pip_conda_connectionfailure_research\n"
                            "  python main.py --web"
                        )
                    else:
                        tip = (
                            "更新 Hosts 失败：没有写入系统 Hosts 的权限。\n"
                            f"目标文件：{hosts_path}\n"
                            "解决方法：用 sudo 重新启动后再试：\n"
                            "  sudo python main.py --web"
                        )
                    _log(job, 'error', tip)
                    _fail_job(job, tip)
                    return
                _fail_job(job, '更新 Hosts 失败（请查看日志与诊断报告）')
                return
            _finish_job(job, {'message': 'GitHub Hosts 更新成功'})
            return

        if action == 'terminal_proxy':
            port = params.get('port') or detect_proxy_port()
            _log(job, 'info', f'生成终端代理命令: port={port}')
            _set_progress(job, 30, '生成命令')
            _, output = _capture_stdout(generate_terminal_proxy_commands, port)
            _log_captured_output(job, output)
            _finish_job(job, {'message': '终端代理命令已生成', 'output': _strip_ansi(output)})
            return

        if action == 'lan_guide':
            port = params.get('port') or detect_proxy_port()
            _log(job, 'info', f'生成局域网共享向导: port={port}')
            _set_progress(job, 30, '生成向导')
            _, output = _capture_stdout(generate_lan_proxy_guide, port)
            _log_captured_output(job, output)
            _finish_job(job, {'message': '局域网共享向导已生成', 'output': _strip_ansi(output)})
            return

        if action == 'apply_template':
            template_key = params.get('template') or params.get('name')
            port = params.get('port') or detect_proxy_port()
            mode = params.get('mode')
            _log(job, 'info', f'应用模板: {template_key}')
            _set_progress(job, 20, '应用模板')
            result, output = _capture_stdout(apply_template, template_key, port, mode)
            _log_captured_output(job, output)
            _finish_job(job, {'message': '模板已应用', 'result': result})
            return

        if action == 'plugin_run':
            name = params.get('name') or params.get('plugin')
            port = params.get('port') or detect_proxy_port()
            _log(job, 'info', f'运行插件: {name}')
            _set_progress(job, 20, '运行插件')
            ctx = {'port': str(port), 'platform': sys.platform, 'cwd': os.getcwd()}
            result, output = _capture_stdout(run_plugin, name, ctx)
            _log_captured_output(job, output)
            _finish_job(job, {'message': '插件已运行', 'result': result})
            return

        if action == 'analyze_project':
            path = params.get('path')
            _log(job, 'info', f'正在分析项目路径: {path}')
            _set_progress(job, 30, '扫描依赖文件')
            try:
                result = analyze_project_path(path)
                _log(job, 'success', f'分析完成: 找到 {len(result["deps"])} 个依赖配置')
                _finish_job(job, {'message': '分析完成', 'analysis': result})
            except Exception as e:
                _fail_job(job, str(e))
            return

        if action == 'install_project':
            path = params.get('path')
            env_type = params.get('envType')
            _log(job, 'info', f'开始构建环境: {env_type} -> {path}')
            _set_progress(job, 10, '初始化环境')
            
            if env_type == 'conda':
                msg, output = _capture_stdout(create_conda_and_install, path)
            else:
                msg, output = _capture_stdout(create_venv_and_install, path)
            
            _log_captured_output(job, output)
            _finish_job(job, {'message': msg})
            return

        if action == 'quick_install':
            pkg = params.get('pkg')
            _log(job, 'info', f'快速安装: {pkg}')
            _set_progress(job, 10, '下载安装中')
            msg, output = _capture_stdout(quick_install_pkg, pkg)
            _log_captured_output(job, output)
            _finish_job(job, {'message': msg})
            return

        if action == 'install_suite':
            suite = params.get('suite')
            target = params.get('target')
            env_name = params.get('env_name')
            custom_packages = params.get('custom_packages')
            
            _log(job, 'info', f'正在安装套件: {suite} -> {target}')
            if custom_packages:
                _log(job, 'info', f'自定义包列表 ({len(custom_packages)}个): {", ".join(custom_packages[:5])}...')
                 
            _set_progress(job, 10, '初始化环境与依赖')
            try:
                msg, output = _capture_stdout(install_suite, suite, target, env_name, custom_packages)
                _log_captured_output(job, output)
                _finish_job(job, {'message': msg})
            except Exception as e:
                _fail_job(job, str(e))
            return

        if action == 'apply_config':
            module = params.get('module')
            mode = params.get('mode')
            port = params.get('port')
            _log(job, 'info', f'准备应用配置: module={module}, mode={mode}')
            _set_progress(job, 20, '应用配置')

            if module == 'python':
                if mode == 'mirror':
                    _log(job, 'info', '配置 Pip 镜像')
                    set_pip_mirror()
                    _set_progress(job, 45, 'Pip 镜像完成')
                    _log(job, 'info', '配置 Conda 镜像')
                    set_conda_mirror()
                    _set_progress(job, 70, 'Conda 镜像完成')
                elif mode == 'proxy':
                    _log(job, 'info', f'配置 Pip 代理: {port}')
                    set_pip_proxy(port)
                    _set_progress(job, 45, 'Pip 代理完成')
                    _log(job, 'info', f'配置 Conda 代理: {port}')
                    set_conda_proxy(port)
                    _set_progress(job, 70, 'Conda 代理完成')
                else:
                    raise ValueError('unknown python mode')

            elif module == 'node':
                if mode == 'mirror':
                    _log(job, 'info', '配置 Node 镜像')
                    set_node_mirror()
                elif mode == 'proxy':
                    _log(job, 'info', f'配置 Node 代理: {port}')
                    set_node_proxy(port)
                else:
                    raise ValueError('unknown node mode')
                _set_progress(job, 75, 'Node 配置完成')

            elif module == 'git':
                if mode != 'proxy':
                    raise ValueError('unknown git mode')
                _log(job, 'info', f'配置 GitHub 智能分流: {port}')
                set_git_proxy(port)
                _set_progress(job, 80, 'Git 配置完成')

            elif module == 'go':
                _log(job, 'info', '配置 GOPROXY')
                set_go_proxy()
                _set_progress(job, 80, 'Go 配置完成')

            elif module == 'docker':
                _log(job, 'info', '配置 Docker 镜像加速')
                set_docker_mirror()
                _set_progress(job, 80, 'Docker 配置完成')

            else:
                raise ValueError('unknown module')

            message = f'{module} 配置已应用 ({mode})'
            _log(job, 'success', message)
            _finish_job(job, {'message': message})
            return

        raise ValueError('unknown action')

    except Exception as e:
        _log(job, 'error', str(e))
        _fail_job(job, str(e))

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/status'):
            body = json.dumps(
                {
                    'is_admin': _is_admin(),
                    'platform': sys.platform,
                    'version': APP_VERSION,
                    'update': UPDATE_INFO,
                },
                ensure_ascii=False,
            ).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/sys_info'):
            info = get_system_info()
            body = json.dumps({'info': info}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/suite_details'):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            suite_name = (params.get('suite') or [''])[0]
            
            suites = get_all_suites()
            if suite_name and suite_name in suites:
                data = suites[suite_name]
            else:
                data = {'error': 'suite not found'}
                
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/templates'):
            body = json.dumps({'templates': list_templates()}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/plugins'):
            body = json.dumps({'plugins': list_plugins()}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/api/stream'):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            job_id = (params.get('job_id') or [''])[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id)

            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()

            if not job:
                self.wfile.write(b"data: {\"type\":\"error\",\"error\":\"job not found\"}\n\n")
                self.wfile.flush()
                return

            while True:
                try:
                    event = job['events'].get(timeout=15)
                    payload = json.dumps(event, ensure_ascii=False).encode('utf-8')
                    self.wfile.write(b"data: " + payload + b"\n\n")
                    self.wfile.flush()
                    if event.get('type') in ('done', 'error'):
                        return
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    if job.get('status') in ('done', 'error'):
                        return
                except Exception:
                    return

        if self.path.startswith('/api/report'):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            job_id = (params.get('job_id') or [''])[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'job not found'}).encode())
                return

            report = {
                'id': job['id'],
                'action': job['action'],
                'params': job['params'],
                'status': job['status'],
                'progress': job['progress'],
                'created_at_ms': job['created_at_ms'],
                'updated_at_ms': job['updated_at_ms'],
                'result': job['result'],
                'error': job['error'],
                'logs': job['logs'],
            }
            body = json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename=\"diagnostic_{job_id}.json\"')
            self.end_headers()
            self.wfile.write(body)
            return

        try:
            return super().do_GET()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            pass

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
        
        if action == 'start_job':
            job_action = data.get('action')
            params = data.get('params') or {}
            allowed = {'detect_port', 'apply_config', 'update_hosts', 'terminal_proxy', 'lan_guide', 'apply_template', 'plugin_run', 'analyze_project', 'install_project', 'quick_install', 'install_suite'}
            if job_action not in allowed:
                return {'status': 'error', 'error': 'unsupported action'}
            job = _new_job(job_action, params)
            _push_event(job, {'type': 'progress', 'value': 0, 'title': '排队'})
            t = threading.Thread(target=_run_job, args=(job['id'],), daemon=True)
            t.start()
            return {'status': 'started', 'job_id': job['id']}

        if action == 'relaunch_admin':
            if not sys.platform.startswith("win"):
                return {'status': 'error', 'error': 'only supported on windows'}
            if _is_admin():
                return {'status': 'ok', 'message': 'already admin'}
            ok = _relaunch_web_as_admin()
            if ok:
                threading.Thread(target=lambda: (time.sleep(0.8), os._exit(0)), daemon=True).start()
                return {'status': 'ok', 'message': 'relaunching'}
            return {'status': 'error', 'error': 'failed to relaunch as admin'}

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
        pass

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def launch_web_ui():
    Handler = RequestHandler
    print(f"正在启动 Web 界面: http://localhost:{PORT}")
    print("请在浏览器中查看...")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{PORT}")

    threading.Thread(target=_refresh_update_info, daemon=True).start()
    
    with ThreadingTCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nWeb 服务已停止")
