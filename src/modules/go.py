from ..core.utils import run_command, Colors

def set_go_proxy(source="goproxy.cn"):
    """Sets GOPROXY environment variable."""
    proxies = {
        "goproxy.cn": "https://goproxy.cn,direct",
        "aliyun": "https://mirrors.aliyun.com/goproxy/,direct",
    }
    url = proxies.get(source, proxies["goproxy.cn"])
    
    Colors.print_info(f"正在配置 Go (GOPROXY) 为 {url}...")
    
    if run_command("go version", capture_output=True):
        run_command(f"go env -w GOPROXY={url}")
        Colors.print_success("GOPROXY 已配置")
    else:
        Colors.print_warning("未检测到 Go 环境，跳过配置")

def unset_go_proxy():
    Colors.print_info("正在清除 Go 配置...")
    if run_command("go version", capture_output=True):
        run_command("go env -u GOPROXY")
        Colors.print_success("Go 配置已恢复默认")
