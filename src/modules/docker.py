import json
import os
import platform
from pathlib import Path
from ..core.utils import Colors

def get_docker_config_path():
    if platform.system() == "Windows":
        return Path.home() / ".docker" / "daemon.json"
    elif platform.system() == "Linux":
        return Path("/etc/docker/daemon.json")
    return None

def set_docker_mirror(source="aliyun"):
    """Configures Docker registry mirrors."""
    # Note: This is complex because mirrors often require authentication or are private.
    # We will use some well-known public mirrors.
    mirrors = [
        "https://docker.m.daocloud.io",
        "https://huecker.io",
        "https://mirror.ccs.tencentyun.com"
    ]
    
    config_path = get_docker_config_path()
    if not config_path:
        Colors.print_warning("不支持的操作系统或找不到 Docker 配置文件路径")
        return

    Colors.print_info(f"正在配置 Docker 镜像源...")
    
    try:
        data = {}
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                pass
        
        data["registry-mirrors"] = mirrors
        
        # Ensure directory exists (for Windows user config)
        if platform.system() == "Windows":
             config_path.parent.mkdir(parents=True, exist_ok=True)
             
        # On Linux, this usually requires sudo, which we can't easily do from python script without escalation.
        # So we just print instructions for Linux if not root.
        if platform.system() == "Linux" and os.geteuid() != 0:
            Colors.print_warning("Linux 下修改 Docker 配置需要 root 权限。请手动将以下内容写入 /etc/docker/daemon.json:")
            print(json.dumps(data, indent=4))
            return

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        Colors.print_success(f"Docker 镜像配置已更新: {config_path}")
        Colors.print_info("请重启 Docker 服务以生效 (Windows: 重启 Docker Desktop; Linux: sudo systemctl restart docker)")
        
    except Exception as e:
        Colors.print_error(f"Docker 配置失败: {str(e)}")
