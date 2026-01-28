from ..core.utils import run_command, Colors

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

def get_git_config(key):
    res = run_command(f"git config --global --get {key}")
    if res and res.returncode == 0:
        return res.stdout.strip()
    return None

def diagnose_git_github(port):
    Colors.print_info("正在诊断 Git - GitHub 连接质量...")
    
    # 1. Check DNS resolution (Direct)
    Colors.print_info("1. 检查 DNS 解析 (github.com)...")
    res_dns = run_command("nslookup github.com")
    if res_dns and "Address" in res_dns.stdout:
        print(res_dns.stdout.strip())
    else:
        Colors.print_warning("DNS 解析可能存在问题")

    # 2. Check Ping (Direct)
    Colors.print_info("2. 检查 Ping (直连)...")
    res_ping = run_command("ping github.com -n 4") # Windows
    if res_ping:
        print(res_ping.stdout.strip())

    # 3. Check Proxy Connection
    Colors.print_info(f"3. 检查代理连接 (端口 {port})...")
    from ..core.utils import measure_latency
    t = measure_latency("https://github.com", proxy=f"http://127.0.0.1:{port}")
    if t != float('inf'):
        Colors.print_success(f"代理连接成功，延迟: {t:.0f}ms")
    else:
        Colors.print_error("代理连接失败，请检查 VPN 是否开启")
