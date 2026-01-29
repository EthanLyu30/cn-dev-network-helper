import os
import shutil
import time
from pathlib import Path
from .utils import Colors, run_command

BACKUP_DIR = Path(".backup")

def ensure_backup_dir():
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir()

def backup_config(name, config_path):
    """Backs up a specific configuration file."""
    ensure_backup_dir()
    if os.path.exists(config_path):
        timestamp = int(time.time())
        backup_path = BACKUP_DIR / f"{name}_{timestamp}.bak"
        shutil.copy2(config_path, backup_path)
        Colors.print_success(f"已备份 {name} 到 {backup_path}")
        return str(backup_path)
    return None

def backup_git_config():
    """Backs up global .gitconfig."""
    home = Path.home()
    gitconfig = home / ".gitconfig"
    if gitconfig.exists():
        backup_config("gitconfig", gitconfig)
    else:
        Colors.print_info("未找到 .gitconfig，跳过备份")

def backup_pip_config():
    """Backs up pip config."""
    # Location varies by OS, simplified for Windows/Linux
    home = Path.home()
    if os.name == 'nt':
        pip_conf = home / "pip" / "pip.ini"
        if not pip_conf.exists():
             pip_conf = home / "AppData" / "Roaming" / "pip" / "pip.ini"
    else:
        pip_conf = home / ".config" / "pip" / "pip.conf"
        if not pip_conf.exists():
            pip_conf = home / ".pip" / "pip.conf"
            
    if pip_conf.exists():
        backup_config("pip_conf", pip_conf)

def backup_condarc():
    """Backs up .condarc."""
    home = Path.home()
    condarc = home / ".condarc"
    if condarc.exists():
        backup_config("condarc", condarc)

def backup_all():
    Colors.print_header("正在备份当前配置...")
    backup_git_config()
    backup_pip_config()
    backup_condarc()
    Colors.print_success("备份完成！")
