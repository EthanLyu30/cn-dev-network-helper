from ..core.utils import run_command, Colors

def set_pip_mirror(source="tsinghua"):
    mirrors = {
        "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "aliyun": "https://mirrors.aliyun.com/pypi/simple/",
    }
    url = mirrors.get(source, mirrors["tsinghua"])
    Colors.print_info(f"正在配置 Pip 为镜像模式 ({source})...")
    run_command("pip config unset global.proxy") 
    res = run_command(f"pip config set global.index-url {url}")
    if res and res.returncode == 0:
        Colors.print_success("Pip 镜像模式配置成功")

def set_pip_proxy(port):
    Colors.print_info(f"正在配置 Pip 为代理模式 (官方源 + 代理)...")
    run_command("pip config unset global.index-url") 
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
        "conda config --remove-key proxy_servers", 
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
        "conda config --remove-key channels",
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

def smart_install_requirements(port):
    import os
    if not os.path.exists("requirements.txt"):
        Colors.print_error("未找到 requirements.txt 文件")
        return

    Colors.print_info("正在尝试使用当前配置安装依赖...")
    # Try install with current config. 
    # Note: subprocess.run with stdout=None prints to console.
    res = run_command("pip install -r requirements.txt", capture_output=False)
    
    if res and res.returncode != 0:
        Colors.print_warning("安装失败！可能因为缺少镜像源或包不存在")
        choice = input(f"是否尝试切换到代理模式 (端口 {port}) 重试？(y/n): ").strip().lower()
        if choice == 'y':
            set_pip_proxy(port)
            Colors.print_info("正在使用代理模式重试安装...")
            run_command("pip install -r requirements.txt", capture_output=False)
            Colors.print_info("提示：安装完成后，建议恢复为镜像模式以提高日常下载速度。")
    else:
        Colors.print_success("依赖安装成功！")
