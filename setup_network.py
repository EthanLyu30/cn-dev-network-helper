import os
import sys
import subprocess
import platform
import json
import time
import socket
import urllib.request
from pathlib import Path

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
    """Detects the active proxy port on localhost by checking common ports or Windows registry."""
    Colors.print_info("正在自动检测代理端口...")
    
    # 1. Check Windows Registry (most accurate for system proxy)
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

    # 2. Port Scan (Fallback)
    common_ports = [7890, 7897, 1080, 10808, 10809, 8888]
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
    """Tests connection speeds and recommends the best configuration."""
    Colors.print_header("正在进行网络测速与诊断")
    
    # 1. Test Official Source (Direct) - Baseline
    print(f"1. 基准测试: PyPI 官方源 (直连)...", end="", flush=True)
    official_direct_latency = measure_latency("https://pypi.org/simple")
    print(f" {official_direct_latency:.0f}ms" if official_direct_latency != float('inf') else " ❌ 超时/失败 (正常现象)")

    # 2. Test Official Source (via Proxy) - Proxy Mode
    proxy_url = f"http://127.0.0.1:{port}"
    print(f"2. 代理模式: PyPI 官方源 (代理 {port})...", end="", flush=True)
    pypi_proxy_latency = measure_latency("https://pypi.org/simple", proxy_url)
    print(f" {pypi_proxy_latency:.0f}ms" if pypi_proxy_latency != float('inf') else " ❌ 连接失败 (请检查代理)")

    # 3. Test Mirror Source (Direct) - Mirror Mode
    print(f"3. 镜像模式: 清华镜像源 (直连)...", end="", flush=True)
    mirror_latency = measure_latency("https://pypi.tuna.tsinghua.edu.cn/simple")
    print(f" {mirror_latency:.0f}ms" if mirror_latency != float('inf') else " ❌ 连接失败")

    # Recommendation Logic
    if pypi_proxy_latency == float('inf') and mirror_latency == float('inf'):
        Colors.print_error("\n警告：所有源均无法连接，请检查网络设置！")
        return "mirror" # Fallback
    
    # Analyze results
    best_mode = "mirror"
    reason = ""
    
    if mirror_latency < pypi_proxy_latency:
        best_mode = "mirror"
        diff = pypi_proxy_latency - mirror_latency
        if pypi_proxy_latency == float('inf'):
             reason = "国内镜像源可用，而代理模式无法连接官方源。"
        else:
             reason = f"国内镜像源比代理模式快 {diff:.0f}ms。"
    else:
        best_mode = "proxy"
        diff = mirror_latency - pypi_proxy_latency
        if mirror_latency == float('inf'):
            reason = "国内镜像源不可用，必须使用代理模式 (VPN)。"
        else:
            reason = f"代理连接官方源比国内镜像快 {diff:.0f}ms (罕见但存在)。"

    print(f"\n💡 诊断结果: {reason}")
    if best_mode == "proxy":
        Colors.print_success(">>> 推荐方案: [代理模式] (即 VPN 模式，解决缺包问题)")
    else:
        Colors.print_success(">>> 推荐方案: [镜像模式] (大多数情况下的速度之王)")
        
    return best_mode

def smart_install_requirements(port):
    """Smartly installs requirements.txt using the best available method."""
    Colors.print_header("智能依赖安装助手")
    
    # 1. Find requirements.txt
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        req_file = input(f"未找到默认 requirements.txt，请输入文件路径: ").strip()
        if not os.path.exists(req_file):
            Colors.print_error("文件不存在！")
            return

    # 2. Try Mirror Install First (Default)
    Colors.print_info("尝试方案 A: 使用国内镜像源极速安装...")
    mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    cmd_mirror = f"pip install -r \"{req_file}\" -i {mirror_url}"
    
    res = run_command(cmd_mirror, capture_output=False) # Show output to user
    
    if res and res.returncode == 0:
        Colors.print_success("安装成功！(使用镜像源)")
        return

    # 3. Fallback to Proxy Install
    Colors.print_warning("镜像源安装失败 (可能缺少部分包)。")
    choice = input(f"是否尝试方案 B: 使用代理模式 (VPN) 重试? (y/n): ").strip().lower()
    
    if choice == 'y':
        Colors.print_info(f"尝试方案 B: 使用代理模式安装 (端口 {port})...")
        cmd_proxy = f"pip install -r \"{req_file}\" --proxy http://127.0.0.1:{port}"
        res = run_command(cmd_proxy, capture_output=False)
        
        if res and res.returncode == 0:
            Colors.print_success("安装成功！(使用代理模式)")
        else:
            Colors.print_error("代理模式安装也失败了，请检查报错信息。")
    else:
        Colors.print_info("操作已取消。")

def diagnose_git_github(port):
    """Specifically diagnoses GitHub connectivity for Git."""
    Colors.print_header("Git -> GitHub 连接专项诊断")
    
    # 1. Test Direct Connection
    print(f"1. 直连测试 (不走代理)...", end="", flush=True)
    direct_latency = measure_latency("https://github.com")
    print(f" {direct_latency:.0f}ms" if direct_latency != float('inf') else " ❌ 连接超时/阻断")
    
    # 2. Test Proxy Connection
    print(f"2. 代理测试 (端口 {port})...", end="", flush=True)
    proxy_latency = measure_latency("https://github.com", f"http://127.0.0.1:{port}")
    print(f" {proxy_latency:.0f}ms" if proxy_latency != float('inf') else " ❌ 连接失败")
    
    # 3. Current Config Check
    current_proxy = get_git_config("http.https://github.com.proxy")
    print(f"\n当前 Git 配置: ", end="")
    if current_proxy:
        print(f"{Colors.GREEN}已开启智能代理 ({current_proxy}){Colors.ENDC}")
        if str(port) not in current_proxy:
            Colors.print_warning(f"注意：Git 配置的端口 ({current_proxy}) 与当前检测到的端口 ({port}) 不一致！")
    else:
        print(f"{Colors.WARNING}未配置代理 (直连模式){Colors.ENDC}")
        
    # 4. Recommendation
    if proxy_latency < direct_latency:
        Colors.print_success(f"\n>>> 建议: 开启 Git 智能代理 (因为代理速度快 {direct_latency - proxy_latency:.0f}ms)")
        return True # Recommend enabling
    elif direct_latency != float('inf') and proxy_latency == float('inf'):
        Colors.print_warning("\n>>> 建议: 保持直连 (你的代理似乎连不上 GitHub)")
        return False
    else:
        print("\n>>> 建议: 维持现状")
        return False

def get_git_config(key):
    res = run_command(f"git config --global --get {key}")
    if res and res.returncode == 0:
        return res.stdout.strip()
    return None

def set_git_proxy(port):
    Colors.print_info(f"正在配置 Git 智能分流 (GitHub 走代理 localhost:{port})...")
    run_command("git config --global --unset http.proxy")
    run_command("git config --global --unset https.proxy")
    cmd = f"git config --global http.https://github.com.proxy http://127.0.0.1:{port}"
    res = run_command(cmd)
    if res and res.returncode == 0:
        Colors.print_success(f"Git 配置成功！仅 github.com 走端口 {port}")
    else:
        Colors.print_error("Git 配置失败")

def unset_git_proxy():
    Colors.print_info("正在清除 Git 代理配置...")
    run_command("git config --global --unset http.proxy")
    run_command("git config --global --unset https.proxy")
    run_command("git config --global --unset http.https://github.com.proxy")
    Colors.print_success("Git 代理已清除")

def set_pip_mirror(source="tsinghua"):
    mirrors = {
        "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "aliyun": "https://mirrors.aliyun.com/pypi/simple/",
    }
    url = mirrors.get(source, mirrors["tsinghua"])
    Colors.print_info(f"正在配置 Pip 为镜像模式 ({source})...")
    run_command("pip config unset global.proxy") # Ensure no proxy
    res = run_command(f"pip config set global.index-url {url}")
    if res and res.returncode == 0:
        Colors.print_success("Pip 镜像模式配置成功")

def set_pip_proxy(port):
    Colors.print_info(f"正在配置 Pip 为代理模式 (官方源 + 代理)...")
    run_command("pip config unset global.index-url") # Reset to official
    res = run_command(f"pip config set global.proxy http://127.0.0.1:{port}")
    if res and res.returncode == 0:
        Colors.print_success(f"Pip 代理模式配置成功 (端口 {port})")

def unset_pip_config():
    Colors.print_info("正在恢复 Pip 默认配置...")
    run_command("pip config unset global.index-url")
    run_command("pip config unset global.proxy")
    Colors.print_success("Pip 已恢复默认")

def set_conda_mirror():
    Colors.print_info("正在配置 Conda 为镜像模式 (清华源)...")
    commands = [
        "conda config --set show_channel_urls yes",
        "conda config --remove-key channels",
        "conda config --remove-key proxy_servers", # Ensure no proxy
        "conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/",
        "conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/",
        "conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/",
    ]
    for cmd in commands:
        run_command(cmd)
    Colors.print_success("Conda 镜像模式配置成功")

def set_conda_proxy(port):
    Colors.print_info(f"正在配置 Conda 为代理模式 (官方源 + 代理)...")
    commands = [
        "conda config --remove-key channels", # Reset to defaults
        "conda config --add channels defaults",
        f"conda config --set proxy_servers.http http://127.0.0.1:{port}",
        f"conda config --set proxy_servers.https http://127.0.0.1:{port}"
    ]
    for cmd in commands:
        run_command(cmd)
    Colors.print_success(f"Conda 代理模式配置成功 (端口 {port})")

def unset_conda_config():
    Colors.print_info("正在恢复 Conda 默认配置...")
    run_command("conda config --remove-key channels")
    run_command("conda config --remove-key proxy_servers")
    run_command("conda config --add channels defaults")
    Colors.print_success("Conda 已恢复默认")

def check_status():
    Colors.print_header("当前配置状态")
    # Git
    git_smart = get_git_config("http.https://github.com.proxy")
    print(f"Git:   {'✅ 智能代理 (' + git_smart + ')' if git_smart else '⬜ 直连/默认'}")
    
    # Pip
    pip_idx = run_command("pip config get global.index-url")
    pip_pxy = run_command("pip config get global.proxy")
    pip_status = "⬜ 默认"
    if pip_idx and pip_idx.stdout.strip(): pip_status = f"⚡ 镜像模式 ({pip_idx.stdout.strip()})"
    if pip_pxy and pip_pxy.stdout.strip(): pip_status = f"🚀 代理模式 ({pip_pxy.stdout.strip()})"
    print(f"Pip:   {pip_status}")

    # Conda
    conda_pxy = run_command("conda config --get proxy_servers.http")
    conda_status = "⬜ 默认/镜像"
    if conda_pxy and "http" in conda_pxy.stdout: conda_status = f"🚀 代理模式"
    print(f"Conda: {conda_status}")

def main():
    while True:
        Colors.print_header("全能网络配置助手 v2.0")
        print("1. [智能推荐] 自动检测端口 + 测速 + 推荐最佳配置")
        print("2. [模式切换] 强制使用 **镜像模式** (适合大多数情况)")
        print("3. [模式切换] 强制使用 **代理模式** (适合解决缺失包/国外环境)")
        print("4. [一键还原] 清除所有配置")
        print("5. [状态检查] 查看当前配置")
        print("6. [依赖安装] 智能安装 requirements.txt (自动重试)")
        print("7. [Git诊断] 专项检测 GitHub 连接延迟与建议")
        print("0. 退出")
        
        choice = input(f"\n{Colors.BOLD}请输入选项: {Colors.ENDC}").strip()
        
        if choice == '0':
            sys.exit(0)
            
        elif choice == '1':
            port = detect_proxy_port()
            rec = recommend_config(port)
            
            print(f"\n推荐方案: {Colors.BOLD}{'代理模式' if rec == 'proxy' else '镜像模式'}{Colors.ENDC}")
            confirm = input("是否应用此方案? (y/n): ").strip().lower()
            if confirm == 'y':
                set_git_proxy(port) # Git always smart proxy
                if rec == 'proxy':
                    set_pip_proxy(port)
                    set_conda_proxy(port)
                else:
                    set_pip_mirror()
                    set_conda_mirror()
                    
        elif choice == '2':
            set_git_proxy(detect_proxy_port())
            set_pip_mirror()
            set_conda_mirror()
            
        elif choice == '3':
            port = detect_proxy_port()
            set_git_proxy(port)
            set_pip_proxy(port)
            set_conda_proxy(port)
            
        elif choice == '4':
            unset_git_proxy()
            unset_pip_config()
            unset_conda_config()
            
        elif choice == '5':
            check_status()
            input("\n按回车键继续...")

        elif choice == '6':
            port = detect_proxy_port()
            smart_install_requirements(port)
            input("\n按回车键返回主菜单...")

        elif choice == '7':
            port = detect_proxy_port()
            should_enable = diagnose_git_github(port)
            if should_enable:
                confirm = input(f"\n是否立即配置 Git 代理 (端口 {port})? (y/n): ").strip().lower()
                if confirm == 'y':
                    set_git_proxy(port)
            input("\n按回车键返回主菜单...")
            
        if choice in ['1', '2', '3', '4']:
             Colors.print_success("操作已完成！")
             input("\n按回车键返回主菜单...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
