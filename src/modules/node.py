from ..core.utils import run_command, Colors

def set_node_mirror(source="taobao"):
    """Sets npm/yarn/pnpm mirror."""
    mirrors = {
        "taobao": "https://registry.npmmirror.com",
        "tencent": "https://mirrors.cloud.tencent.com/npm/",
    }
    url = mirrors.get(source, mirrors["taobao"])
    
    Colors.print_info(f"正在配置 Node.js (npm/yarn/pnpm) 镜像为 {source}...")
    
    # npm
    if run_command("npm --version", capture_output=True):
        run_command(f"npm config set registry {url}")
        Colors.print_success(f"npm 镜像已设置: {url}")
    
    # yarn
    if run_command("yarn --version", capture_output=True):
        run_command(f"yarn config set registry {url}")
        Colors.print_success(f"yarn 镜像已设置: {url}")

    # pnpm
    if run_command("pnpm --version", capture_output=True):
        run_command(f"pnpm config set registry {url}")
        Colors.print_success(f"pnpm 镜像已设置: {url}")

def set_node_proxy(port):
    """Sets npm/yarn/pnpm proxy."""
    proxy_url = f"http://127.0.0.1:{port}"
    Colors.print_info(f"正在配置 Node.js 代理: {proxy_url}...")
    
    cmds = [
        f"npm config set proxy {proxy_url}",
        f"npm config set https-proxy {proxy_url}",
        f"yarn config set proxy {proxy_url}",
        f"yarn config set https-proxy {proxy_url}",
        f"pnpm config set proxy {proxy_url}",
        f"pnpm config set https-proxy {proxy_url}",
    ]
    
    for cmd in cmds:
        tool = cmd.split()[0]
        if run_command(f"{tool} --version", capture_output=True):
            run_command(cmd)
            
    Colors.print_success("Node.js 代理已配置")

def unset_node_config():
    Colors.print_info("正在清除 Node.js 配置...")
    cmds = [
        "npm config delete registry",
        "npm config delete proxy",
        "npm config delete https-proxy",
        "yarn config delete registry",
        "yarn config delete proxy",
        "yarn config delete https-proxy",
        "pnpm config delete registry",
        "pnpm config delete proxy",
        "pnpm config delete https-proxy",
    ]
    for cmd in cmds:
        tool = cmd.split()[0]
        if run_command(f"{tool} --version", capture_output=True):
            run_command(cmd)
    Colors.print_success("Node.js 配置已恢复默认")
