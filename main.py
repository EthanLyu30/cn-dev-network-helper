import sys
import argparse
from src.core.utils import Colors, detect_proxy_port, recommend_config
from src.core.backup import backup_all
from src.modules.git import set_git_proxy, unset_git_proxy, diagnose_git_github
from src.modules.python import (
    set_pip_mirror, set_pip_proxy, unset_pip_config,
    set_conda_mirror, set_conda_proxy, unset_conda_config, smart_install_requirements
)
from src.modules.node import set_node_mirror, set_node_proxy, unset_node_config
from src.modules.go import set_go_proxy, unset_go_proxy
from src.modules.docker import set_docker_mirror

def main():
    parser = argparse.ArgumentParser(description="全能开发环境网络助手")
    parser.add_argument("--web", action="store_true", help="启动 Web 可视化界面 (推荐)")
    args = parser.parse_args()

    if args.web:
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
        print("5. [工具] 备份配置 / 依赖安装 / Git诊断")
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
                backup_all()
                set_git_proxy(port)
                if rec == 'proxy':
                    set_pip_proxy(port)
                    set_conda_proxy(port)
                else:
                    set_pip_mirror()
                    set_conda_mirror()
                    
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
            sub = input("请选择: ").strip()
            if sub == '1': backup_all()
            elif sub == '2': smart_install_requirements(detect_proxy_port())
            elif sub == '3': diagnose_git_github(detect_proxy_port())

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
