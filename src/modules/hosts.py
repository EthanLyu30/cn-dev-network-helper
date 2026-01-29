import os
import platform
import urllib.request
import ctypes
from src.core.utils import Colors

# Remote Hosts Source (Using GitHub520)
HOSTS_URL = "https://raw.githubusercontent.com/521xueweihan/GitHub520/main/hosts"
START_MARKER = "# Start GitHub520 Host"
END_MARKER = "# End GitHub520 Host"

def is_admin():
    system = platform.system()
    if system == "Windows":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    try:
        return os.geteuid() == 0
    except Exception:
        return False

def get_hosts_path():
    """Returns the path to the system hosts file."""
    system = platform.system()
    if system == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    else:
        # Linux / macOS
        return "/etc/hosts"

def fetch_remote_hosts():
    """Fetches the latest GitHub hosts from the remote source."""
    Colors.print_info(f"正在获取最新 GitHub Hosts: {HOSTS_URL} ...")
    try:
        with urllib.request.urlopen(HOSTS_URL, timeout=10) as response:
            content = response.read().decode('utf-8')
            return content
    except Exception as e:
        Colors.print_error(f"获取远程 Hosts 失败: {e}")
        return None

def update_github_hosts():
    """Updates the system hosts file with the latest GitHub hosts."""
    hosts_path = get_hosts_path()
    
    if not os.path.exists(hosts_path):
        Colors.print_error(f"找不到系统 Hosts 文件: {hosts_path}")
        return False

    if platform.system() == "Windows" and not is_admin():
        Colors.print_warning(f"需要管理员权限才能写入 Hosts 文件: {hosts_path}")
        Colors.print_info("请以【管理员身份】运行此脚本/终端后重试")
        return False

    if not os.access(hosts_path, os.W_OK):
        Colors.print_warning(f"没有权限写入 Hosts 文件: {hosts_path}")
        if platform.system() == "Windows":
            Colors.print_info("请尝试以【管理员身份】运行此脚本 (右键 -> 以管理员身份运行)")
        else:
            Colors.print_info("请尝试使用 sudo 运行此脚本: sudo python main.py")
        return False

    new_hosts_content = fetch_remote_hosts()
    if not new_hosts_content:
        return False

    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            current_content = f.read()

        # Construct new content block
        block = f"\n{START_MARKER}\n{new_hosts_content}\n{END_MARKER}\n"

        # Replace existing block or append
        if START_MARKER in current_content and END_MARKER in current_content:
            Colors.print_info("发现已有 GitHub Hosts 配置，正在更新...")
            # Use regex or simple string manipulation
            # Simple split approach
            parts = current_content.split(START_MARKER)
            pre_part = parts[0]
            post_part = parts[1].split(END_MARKER)[-1]
            final_content = pre_part + block.strip() + post_part
        else:
            Colors.print_info("未发现旧配置，正在追加...")
            final_content = current_content + block

        # Write back
        with open(hosts_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        Colors.print_success("GitHub Hosts 更新成功！")
        
        # Flush DNS
        if platform.system() == "Windows":
            os.system("ipconfig /flushdns")
        else:
            # macOS
            if platform.system() == "Darwin":
                os.system("sudo killall -HUP mDNSResponder")
            # Linux (systemd-resolve or nscd, vary widely, skipping usually ok or just advise user)
        
        return True

    except Exception as e:
        Colors.print_error(f"写入 Hosts 文件失败: {e}")
        return False
