import socket
import platform
from src.core.utils import Colors

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_terminal_proxy_commands(port):
    system = platform.system()
    
    Colors.print_header("终端临时代理设置命令")
    print("请复制以下命令并在当前终端中运行 (运行后仅当前窗口有效)：")
    
    if system == "Windows":
        print(f"\n{Colors.BOLD}# PowerShell:{Colors.ENDC}")
        print(f"$env:HTTP_PROXY='http://127.0.0.1:{port}'")
        print(f"$env:HTTPS_PROXY='http://127.0.0.1:{port}'")
        
        print(f"\n{Colors.BOLD}# CMD (Command Prompt):{Colors.ENDC}")
        print(f"set HTTP_PROXY=http://127.0.0.1:{port}")
        print(f"set HTTPS_PROXY=http://127.0.0.1:{port}")
        
        print(f"\n{Colors.BOLD}# Git Bash / WSL:{Colors.ENDC}")
        print(f"export http_proxy=http://127.0.0.1:{port}")
        print(f"export https_proxy=http://127.0.0.1:{port}")
        
    else:
        print(f"\n{Colors.BOLD}# Bash / Zsh:{Colors.ENDC}")
        print(f"export http_proxy=http://127.0.0.1:{port}")
        print(f"export https_proxy=http://127.0.0.1:{port}")
        print(f"export ALL_PROXY=socks5://127.0.0.1:{port}")

    print("\n" + "-"*30)
    print("验证方法: 运行 curl -I https://www.google.com")
    print("-"*30)

def generate_lan_proxy_guide(port):
    local_ip = get_local_ip()
    
    Colors.print_header("局域网代理共享指南")
    Colors.print_info(f"本机局域网 IP: {Colors.BOLD}{local_ip}{Colors.ENDC}")
    Colors.print_info(f"本机代理端口: {Colors.BOLD}{port}{Colors.ENDC}")
    
    print("\n[前提条件]")
    print("1. 确保你的代理软件 (如 v2rayN/Clash) 已开启 '允许来自局域网的连接' (Allow LAN)。")
    print("2. 确保本机防火墙允许该端口的入站连接 (或临时关闭防火墙)。")
    
    print(f"\n[在其他机器上配置]")
    
    print(f"{Colors.BOLD}>>> 方法 A: Git 配置{Colors.ENDC}")
    print(f"git config --global http.proxy http://{local_ip}:{port}")
    print(f"git config --global https.proxy http://{local_ip}:{port}")
    
    print(f"\n{Colors.BOLD}>>> 方法 B: 环境变量 (终端){Colors.ENDC}")
    if platform.system() == "Windows":
        print(f"$env:HTTP_PROXY='http://{local_ip}:{port}'")
        print(f"$env:HTTPS_PROXY='http://{local_ip}:{port}'")
    else:
        print(f"export http_proxy=http://{local_ip}:{port}")
        print(f"export https_proxy=http://{local_ip}:{port}")
        
    print(f"\n{Colors.BOLD}>>> 方法 C: Pip 配置{Colors.ENDC}")
    print(f"pip config set global.proxy http://{local_ip}:{port}")

    print(f"\n{Colors.BOLD}>>> 移动设备配置指南 (手机/平板){Colors.ENDC}")
    print("1. 确保手机与电脑连接同一个 Wi-Fi。")
    print("2. 在手机 Wi-Fi 设置中，找到当前连接的 Wi-Fi，点击详细信息/编辑。")
    print("3. 找到 '代理 (Proxy)' 选项，选择 '手动 (Manual)'。")
    print(f"4. 主机名 (Host) 填写: {Colors.BOLD}{local_ip}{Colors.ENDC}")
    print(f"5. 端口 (Port) 填写: {Colors.BOLD}{port}{Colors.ENDC}")
    print("6. 保存后，手机浏览器即可通过电脑 VPN 上网。")

    Colors.print_warning("注意: 局域网共享依赖于你的网络环境，如果无法连接，请检查防火墙设置。")
