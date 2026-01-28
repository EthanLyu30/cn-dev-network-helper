import sys
import subprocess
import socket
import urllib.request
import time
import platform
import os

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print_header(msg):
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== {msg} ==={Colors.ENDC}")

    @staticmethod
    def print_success(msg):
        print(f"{Colors.GREEN}✔ {msg}{Colors.ENDC}")

    @staticmethod
    def print_info(msg):
        print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")

    @staticmethod
    def print_warning(msg):
        print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

    @staticmethod
    def print_error(msg):
        print(f"{Colors.FAIL}✘ {msg}{Colors.ENDC}")

class ProgressBar:
    def __init__(self, total, prefix='Progress', suffix='Complete', decimals=1, length=50, fill='█'):
        self.total = total
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.length = length
        self.fill = fill
        self.iteration = 0

    def update(self, iteration=None):
        if iteration is not None:
            self.iteration = iteration
        else:
            self.iteration += 1
            
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (self.iteration / float(self.total)))
        filled_length = int(self.length * self.iteration // self.total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        print(f'\r{self.prefix} |{bar}| {percent}% {self.suffix}', end = '\r')
        if self.iteration == self.total: 
            print()

def run_command(command, capture_output=True):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result
    except Exception as e:
        return None

def detect_proxy_port():
    """Detects the active proxy port on localhost by checking common ports, Windows registry, or Env vars."""
    Colors.print_info("正在自动检测代理端口...")
    
    # 1. Check Environment Variables (Universal for Linux/macOS/Windows)
    env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Parse port from "http://127.0.0.1:7890" or "127.0.0.1:7890"
            try:
                if '://' in value:
                    port = value.split(':')[-1].strip('/')
                else:
                    port = value.split(':')[-1].strip('/')
                
                if port.isdigit():
                    Colors.print_success(f"从环境变量 {var} 检测到端口: {port}")
                    return port
            except:
                pass

    # 2. Check Windows Registry (System Proxy)
    if platform.system() == "Windows":
        try:
            import winreg
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
            winreg.CloseKey(key)
            
            if proxy_enable == 1 and proxy_server:
                # Handle "127.0.0.1:7890" or "http=127.0.0.1:7890;https=..."
                if "=" in proxy_server:
                    for part in proxy_server.split(";"):
                        if part.startswith("http=") or part.startswith("https="):
                            return part.split(":")[-1]
                elif ":" in proxy_server:
                    return proxy_server.split(":")[-1]
        except Exception:
            pass

    # 3. Port Scan (Fallback)
    common_ports = [7890, 7897, 1080, 10808, 10809, 8888, 8889, 9999]
    for port in common_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                Colors.print_success(f"检测到活跃端口: {port}")
                return str(port)
    
    Colors.print_warning("未检测到常用代理端口，将使用默认值 7897")
    return "7897"

def measure_latency(url, proxy=None):
    """Measures latency to a URL, optionally via proxy."""
    start_time = time.time()
    try:
        if proxy:
            # Simple proxy handler
            proxy_handler = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
            opener = urllib.request.build_opener(proxy_handler)
            opener.open(url, timeout=5)
        else:
            urllib.request.urlopen(url, timeout=5)
        return (time.time() - start_time) * 1000 # ms
    except Exception:
        return float('inf')

def recommend_config(port):
    """
    Compares latency between direct connection (mirror) and proxy connection (official).
    Returns 'proxy' or 'mirror'.
    """
    Colors.print_info("正在进行网络测速 (赛马机制)...")
    
    # 1. Test Mirror (TUNA) - Direct
    mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    t_mirror = measure_latency(mirror_url)
    
    # 2. Test Official (PyPI) - Proxy
    official_url = "https://pypi.org/simple"
    proxy_url = f"http://127.0.0.1:{port}"
    t_proxy = measure_latency(official_url, proxy=proxy_url)
    
    t_mirror_str = f"{t_mirror:.0f}ms" if t_mirror != float('inf') else "超时"
    t_proxy_str = f"{t_proxy:.0f}ms" if t_proxy != float('inf') else "超时"
    
    print(f"  - 镜像源 (直连): {t_mirror_str}")
    print(f"  - 官方源 (代理): {t_proxy_str}")
    
    if t_proxy < t_mirror:
        return 'proxy'
    else:
        return 'mirror'
