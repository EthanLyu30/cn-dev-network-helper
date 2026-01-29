import sys
import argparse
import os
import ctypes
from src.core.utils import Colors, detect_proxy_port, recommend_config, ProgressBar
from src.core.backup import backup_all
from src.modules.git import set_git_proxy, unset_git_proxy, diagnose_git_github
from src.modules.python import (
    set_pip_mirror, set_pip_proxy, unset_pip_config,
    set_conda_mirror, set_conda_proxy, unset_conda_config, smart_install_requirements
)
from src.modules.node import set_node_mirror, set_node_proxy, unset_node_config
from src.modules.go import set_go_proxy, unset_go_proxy
from src.modules.docker import set_docker_mirror
from src.modules.hosts import update_github_hosts
from src.modules.proxy_tools import generate_terminal_proxy_commands, generate_lan_proxy_guide

def _is_admin():
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def _relaunch_as_admin():
    if os.name != "nt":
        return False
    script_path = os.path.abspath(__file__)
    params = f"\"{script_path}\" --web"
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, os.getcwd(), 1)
        return int(rc) > 32
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="全能开发环境网络助手")
    parser.add_argument("--web", action="store_true", help="启动 Web 可视化界面 (推荐)")
    args = parser.parse_args()

    if args.web:
        if os.name == "nt" and not _is_admin():
            ok = _relaunch_as_admin()
            if ok:
                return
            Colors.print_warning("无法自动以管理员权限启动 Web（可能被策略/环境限制）")
            Colors.print_info("请用 Windows Terminal(管理员) 运行：python main.py --web")
        try:
            from src.web.server import launch_web_ui
            launch_web_ui()
            return
        except ImportError as e:
            Colors.print_error(f"无法启动 Web 界面: {e}")
            return

    while True:
        Colors.print_header("全能网络配置助手 v3.0 (All-in-One)")
        print("1. [智能推荐] 自动检测 + 测速 + 推荐配置 (Python/Git)")
        print("2. [Python] 配置 Pip/Conda (镜像/代理)")
        print("3. [Node.js] 配置 Npm/Yarn (镜像/代理)")
        print("4. [其他] 配置 Git / Go / Docker")
        print("5. [工具] 备份 / 诊断 / Hosts / 代理工具")
        print("6. [还原] 清除所有配置")
        print("0. 退出")
        
        choice = input(f"\n{Colors.BOLD}请输入选项: {Colors.ENDC}").strip().lower()
        
        if choice == '0':
            sys.exit(0)

        elif choice == '1':
            # Smart Recommendation (Legacy Logic)
            port = detect_proxy_port()
            rec = recommend_config(port)
            print(f"\n推荐方案: {Colors.BOLD}{'代理模式' if rec == 'proxy' else '镜像模式'}{Colors.ENDC}")
            if input("是否应用? (y/n): ").lower() == 'y':
                pb = ProgressBar(total=100, prefix='正在配置', suffix='', length=30)
                backup_all()
                pb.update(30)
                set_git_proxy(port)
                pb.update(60)
                if rec == 'proxy':
                    set_pip_proxy(port)
                    set_conda_proxy(port)
                else:
                    set_pip_mirror()
                    set_conda_mirror()
                pb.update(100)
                    
        elif choice == '2': # Python Menu
            print("\n--- Python 配置 ---")
            print("1. 镜像模式 (清华源) [推荐]")
            print("2. 代理模式 (VPN)")
            sub = input("请选择: ").strip()
            if sub == '1':
                set_pip_mirror()
                set_conda_mirror()
            elif sub == '2':
                port = detect_proxy_port()
                set_pip_proxy(port)
                set_conda_proxy(port)

        elif choice == '3': # Node Menu
            print("\n--- Node.js 配置 ---")
            print("1. 镜像模式 (淘宝/腾讯源) [推荐]")
            print("2. 代理模式 (VPN)")
            sub = input("请选择: ").strip()
            if sub == '1': set_node_mirror()
            elif sub == '2': set_node_proxy(detect_proxy_port())

        elif choice == '4': # Other Menu
            print("\n--- 其他工具 ---")
            print("1. Git: 开启 GitHub 智能代理")
            print("2. Go: 设置 GOPROXY")
            print("3. Docker: 设置镜像加速")
            sub = input("请选择: ").strip()
            if sub == '1': set_git_proxy(detect_proxy_port())
            elif sub == '2': set_go_proxy()
            elif sub == '3': set_docker_mirror()

        elif choice == '5': # Tools Menu
            print("\n--- 实用工具 ---")
            print("1. 备份当前所有配置")
            print("2. 智能安装 requirements.txt")
            print("3. Git 连接诊断")
            print("4. 更新 GitHub Hosts (解决 DNS 污染)")
            print("5. 获取终端代理命令 (Terminal Proxy)")
            print("6. 局域网代理共享指南 (LAN Sharing)")
            sub = input("请选择: ").strip()
            if sub == '1': backup_all()
            elif sub == '2': smart_install_requirements(detect_proxy_port())
            elif sub == '3': diagnose_git_github(detect_proxy_port())
            elif sub == '4': update_github_hosts()
            elif sub == '5': generate_terminal_proxy_commands(detect_proxy_port())
            elif sub == '6': generate_lan_proxy_guide(detect_proxy_port())

        elif choice == '6': # Reset
            backup_all()
            unset_git_proxy()
            unset_pip_config()
            unset_conda_config()
            unset_node_config()
            unset_go_proxy()
            Colors.print_success("所有配置已清除")
            
        input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
