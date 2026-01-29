import os
import json
import subprocess
import sys
import time
from ..core.utils import run_command, Colors

def analyze_project_path(path):
    """
    Analyzes a project directory for dependency files.
    """
    if not os.path.exists(path):
        raise ValueError("路径不存在")
    
    files = os.listdir(path)
    deps = []
    
    if "requirements.txt" in files:
        deps.append("requirements.txt (Python)")
    if "environment.yml" in files:
        deps.append("environment.yml (Conda)")
    if "package.json" in files:
        deps.append("package.json (Node.js)")
    if "Pipfile" in files:
        deps.append("Pipfile (Pipenv)")
    if "pyproject.toml" in files:
        deps.append("pyproject.toml (Poetry/Flit)")

    # Check for Conda availability
    has_conda = False
    try:
        subprocess.run(["conda", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        has_conda = True
    except:
        pass

    recommendation = "System Python"
    if "environment.yml" in files:
        recommendation = "Conda Environment"
    elif "requirements.txt" in files:
        recommendation = "Venv (Virtualenv)" if not has_conda else "Conda or Venv"
    
    return {
        "path": path,
        "name": os.path.basename(path),
        "deps": deps,
        "has_conda": has_conda,
        "recommendation": recommendation
    }

def create_venv_and_install(path, stop_event=None):
    """
    Creates a venv in the project directory and installs requirements.
    """
    venv_path = os.path.join(path, ".venv")
    
    # 1. Create Venv
    if not os.path.exists(venv_path):
        print(f"正在创建虚拟环境: {venv_path} ...")
        # Creating venv is usually fast, but let's stream it just in case
        res = run_command(f"\"{sys.executable}\" -m venv \"{venv_path}\"", stream_output=True, stop_event=stop_event)
        if res.returncode != 0:
            raise subprocess.CalledProcessError(res.returncode, "venv creation", output=res.stdout)
    else:
        print(f"虚拟环境已存在: {venv_path}")

    if stop_event and stop_event.is_set(): raise InterruptedError()

    # 2. Install Deps
    pip_exe = os.path.join(venv_path, "Scripts", "pip") if sys.platform == "win32" else os.path.join(venv_path, "bin", "pip")
    
    req_file = os.path.join(path, "requirements.txt")
    if os.path.exists(req_file):
        print("正在安装依赖 (requirements.txt)...")
        # Use mirror if configured globally? 
        # Actually, we should force use mirror here for speed
        mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
        cmd = f"\"{pip_exe}\" install -r \"{req_file}\" -i {mirror_url}"
        res = run_command(cmd, stream_output=True, stop_event=stop_event)
        if res.returncode != 0:
            raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout)
        return {"message": f"环境创建成功！依赖已安装。\n激活命令: {os.path.join(venv_path, 'Scripts', 'activate')}", "env_path": venv_path, "type": "venv", "env_name": os.path.basename(path)}
    else:
        return {"message": f"环境创建成功！但未找到 requirements.txt", "env_path": venv_path, "type": "venv", "env_name": os.path.basename(path)}

def create_conda_and_install(path, stop_event=None):
    """
    Creates a conda env and installs requirements.
    """
    env_name = os.path.basename(path) + "_env"
    
    # Check if env.yml exists
    yml_file = os.path.join(path, "environment.yml")
    
    if os.path.exists(yml_file):
        print(f"正在基于 environment.yml 创建 Conda 环境: {env_name} ...")
        cmd = f"conda env create -f \"{yml_file}\" --name {env_name}"
        res = run_command(cmd, stream_output=True, stop_event=stop_event)
        if res.returncode != 0:
             raise Exception(f"Conda env creation failed: {res.stdout}")
    else:
        print(f"正在创建通用 Conda 环境: {env_name} ...")
        res = run_command(f"conda create -n {env_name} python=3.10 -y", stream_output=True, stop_event=stop_event)
        if res.returncode != 0:
             raise Exception(f"Conda create failed: {res.stdout}")
        
        req_file = os.path.join(path, "requirements.txt")
        if os.path.exists(req_file):
            if stop_event and stop_event.is_set(): raise InterruptedError()
            print("正在安装 pip 依赖...")
            # We need to run pip inside the conda env. 
            # Best way is 'conda run -n name pip install ...'
            mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
            cmd = f"conda run -n {env_name} pip install -r \"{req_file}\" -i {mirror_url}"
            res = run_command(cmd, stream_output=True, stop_event=stop_event)
            if res.returncode != 0:
                raise Exception(f"Pip install failed: {res.stdout}")

    return {"message": f"Conda 环境 {env_name} 创建成功！", "env_name": env_name, "type": "conda"}

import platform
import re

def get_system_info():
    """
    Detects system hardware and OS information.
    Returns: { 'os': str, 'gpu': str, 'cuda': str|None, 'arch': str }
    """
    info = {
        'os': f"{platform.system()} {platform.release()}",
        'arch': platform.machine(),
        'gpu': 'Integrated / Unknown',
        'cuda': None
    }
    
    # 1. GPU Detection (Basic)
    try:
        if sys.platform == 'win32':
            cmd = 'wmic path win32_VideoController get Name'
            out = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            lines = [x.strip() for x in out.splitlines() if x.strip() and 'Name' not in x]
            # Filter out basic display adapters if possible, but keeping all is safer
            if lines:
                info['gpu'] = ' / '.join(lines)
        elif sys.platform == 'darwin':
            if platform.machine() == 'arm64':
                info['gpu'] = 'Apple Silicon (Metal)'
            else:
                info['gpu'] = 'Intel/AMD (Mac)'
    except Exception:
        pass

    # 2. CUDA Detection (NVIDIA Specific)
    try:
        # Try running nvidia-smi
        output = subprocess.check_output(['nvidia-smi'], encoding='utf-8', errors='ignore')
        if 'NVIDIA' in output:
             # Refine GPU name if nvidia-smi gives better info? 
             # Usually wmic is fine for name. Let's just check CUDA version.
             cuda_match = re.search(r'CUDA Version:\s*(\d+\.\d+)', output)
             if cuda_match:
                 info['cuda'] = cuda_match.group(1)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
        
    # 3. Generate Recommendation
    rec = []
    if info['cuda']:
         rec.append(f"🚀 检测到 NVIDIA GPU (CUDA {info['cuda']})，推荐使用 GPU 加速版本。")
    elif info['gpu'] and 'Apple' in info['gpu']:
         rec.append("🍎 检测到 Apple Silicon，推荐使用 MPS (Metal) 加速版本。")
    else:
         rec.append("⚠️ 未检测到高性能独显，推荐使用 CPU 版本或轻量级模型。")
    
    if 'Windows' in info['os']:
         rec.append("💡 Windows 用户建议使用 WSL2 进行大型训练任务。")

    info['recommendation'] = " ".join(rec)

    return info

def install_suite(suite, target, env_name=None, custom_packages=None):
    """
    Installs a suite of packages.
    target: 'pip_current', 'conda_current', 'conda_new'
    """
    mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    sys_info = get_system_info()
    
    print(f"检测到系统环境: {sys_info['os']} / {sys_info['arch']} / {sys_info['gpu']} (CUDA: {sys_info['cuda'] or 'N/A'})")

def get_all_suites(sys_info=None):
    """
    Returns the definition of all available suites, adapted for the hardware.
    """
    if sys_info is None:
        sys_info = get_system_info()

    # Common base for all DL
    base_dl = ['numpy', 'pandas', 'matplotlib', 'scikit-learn', 'jupyterlab', 'tqdm', 'seaborn', 'h5py', 'pillow', 'opencv-python']
    
    suites = {
        'dl_torch': {
            'desc': 'PyTorch 深度学习全家桶',
            'pip_base': base_dl + ['tensorboard', 'gradio', 'transformers', 'datasets', 'accelerate', 'torchmetrics', 'optuna', 'onnx', 'pytorch-lightning'],
            'conda_base': base_dl + ['tensorboard', 'gradio', 'transformers', 'datasets', 'accelerate', 'torchmetrics', 'optuna', 'onnx', 'pytorch-lightning'],
            # PyTorch logic handled separately due to CUDA variants
        },
        'dl_tf': {
            'desc': 'TensorFlow 深度学习全家桶',
            'pip_base': base_dl + ['tensorflow', 'tensorboard', 'keras', 'tensorflow-datasets'],
            'conda_base': base_dl + ['tensorflow', 'tensorboard', 'keras', 'tensorflow-datasets'],
        },
        'web_dev': {
            'desc': 'Python Web 开发 (全栈)',
            'pip_base': ['fastapi', 'uvicorn', 'django', 'flask', 'requests', 'pydantic', 'sqlalchemy', 'python-dotenv', 'redis', 'celery', 'httpx', 'beautifulsoup4', 'gunicorn', 'jinja2', 'marshmallow', 'alembic', 'websockets'],
            'conda_base': ['fastapi', 'uvicorn', 'django', 'flask', 'requests', 'pydantic', 'sqlalchemy', 'python-dotenv', 'redis', 'celery', 'httpx', 'beautifulsoup4', 'gunicorn', 'jinja2', 'marshmallow', 'alembic', 'websockets'],
        },
        'data_science': {
            'desc': '数据科学与大数据分析',
            'pip_base': ['numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'scikit-learn', 'statsmodels', 'openpyxl', 'jupyterlab', 'plotly', 'sympy', 'networkx', 'bokeh', 'lxml', 'xlrd', 'fsspec', 'dask'],
            'conda_base': ['numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn', 'scikit-learn', 'statsmodels', 'openpyxl', 'jupyterlab', 'plotly', 'sympy', 'networkx', 'bokeh', 'lxml', 'xlrd', 'fsspec', 'dask'],
        },
        'app_dev': {
            'desc': '桌面/移动应用开发',
            'pip_base': ['PyQt6', 'kivy', 'buildozer', 'pyinstaller', 'cx_Freeze', 'pyside6', 'briefcase'],
            'conda_base': ['pyqt', 'kivy', 'pyside6'] # buildozer/cx_Freeze often better via pip even in conda
        },
        'spider': {
             'desc': '网络爬虫与数据采集',
             'pip_base': ['requests', 'scrapy', 'beautifulsoup4', 'selenium', 'playwright', 'lxml', 'parsel', 'pyquery', 'aiohttp'],
             'conda_base': ['requests', 'scrapy', 'beautifulsoup4', 'selenium', 'lxml', 'parsel', 'pyquery', 'aiohttp']
        }
    }

    # --- Hardware Adaptation Logic ---
    is_mac_arm = 'Darwin' in sys_info['os'] and 'arm64' in sys_info['arch']
    is_windows = 'Windows' in sys_info['os']

    # 1. Mac Apple Silicon Adaptations
    if is_mac_arm:
        # TensorFlow: Replace 'tensorflow' with 'tensorflow-macos' + 'tensorflow-metal'
        if 'tensorflow' in suites['dl_tf']['pip_base']:
            suites['dl_tf']['pip_base'].remove('tensorflow')
            suites['dl_tf']['pip_base'].extend(['tensorflow-macos', 'tensorflow-metal'])

    # 2. Windows Adaptations
    if is_windows:
        # Remove 'uvloop' if present (it's not in my list, but for safety)
        # Remove 'gunicorn' (Unix only), replace with 'waitress' or just remove
        if 'gunicorn' in suites['web_dev']['pip_base']:
            suites['web_dev']['pip_base'].remove('gunicorn')
            suites['web_dev']['pip_base'].append('waitress') # Compatible alternative
        if 'gunicorn' in suites['web_dev']['conda_base']:
            suites['web_dev']['conda_base'].remove('gunicorn')
            suites['web_dev']['conda_base'].append('waitress')

    return suites

def install_suite(suite, target, env_name=None, custom_packages=None, stop_event=None):
    """
    Installs a suite of packages.
    target: 'pip_current', 'conda_current', 'conda_new'
    custom_packages: list of strings (optional), overrides the default suite packages.
    """
    mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    sys_info = get_system_info()
    
    print(f"检测到系统环境: {sys_info['os']} / {sys_info['arch']} / {sys_info['gpu']} (CUDA: {sys_info['cuda'] or 'N/A'})")
    
    # Pass sys_info to get_all_suites to ensure we get the filtered list
    suites = get_all_suites(sys_info)
    
    if suite not in suites:
        raise ValueError(f"未知套件: {suite}")
        
    # Determine packages to install
    if custom_packages:
        pkgs_pip = list(custom_packages)
        pkgs_conda = list(custom_packages)
    else:
        pkgs_pip = suites[suite].get('pip_base', [])
        pkgs_conda = suites[suite].get('conda_base', [])
    
    # --- PyTorch Special Logic ---
    torch_extra_index = None
    # Check if we should install torch (if suite is dl_torch OR 'torch' is in custom packages)
    should_install_torch = (suite == 'dl_torch')
    
    if should_install_torch:
        # Remove generic torch from list if present to avoid double install with wrong index
        for p in ['torch', 'torchvision', 'torchaudio']:
            if p in pkgs_pip: pkgs_pip.remove(p)
            if p in pkgs_conda: pkgs_conda.remove(p)

        # Determine PyTorch version based on Hardware
        # If CUDA is detected, we assume NVIDIA GPU is present and usable
        if sys_info['cuda']:
            # Mapping CUDA version to PyTorch index
            # Roughly: 11.x -> cu118, 12.x -> cu121
            cuda_ver = float(sys_info['cuda'])
            if cuda_ver >= 12.0:
                print(">>> 推荐: PyTorch CUDA 12.1 版本")
                torch_pkgs = ['torch', 'torchvision', 'torchaudio']
                torch_extra_index = "https://download.pytorch.org/whl/cu121"
                # Conda needs specific channel/package
                conda_torch_cmd = "pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia"
            elif cuda_ver >= 11.0:
                print(">>> 推荐: PyTorch CUDA 11.8 版本")
                torch_pkgs = ['torch', 'torchvision', 'torchaudio']
                torch_extra_index = "https://download.pytorch.org/whl/cu118"
                conda_torch_cmd = "pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia"
            else:
                print(">>> 警告: CUDA 版本过低，推荐使用 CPU 版本或手动安装")
                torch_pkgs = ['torch', 'torchvision', 'torchaudio']
                torch_extra_index = "https://download.pytorch.org/whl/cpu"
                conda_torch_cmd = "pytorch torchvision torchaudio cpuonly -c pytorch"
        elif sys.platform == 'darwin' and platform.machine() == 'arm64':
             print(">>> 推荐: PyTorch (Mac M1/M2 Metal 加速)")
             torch_pkgs = ['torch', 'torchvision', 'torchaudio']
             # Mac usually uses default index
             torch_extra_index = None 
             conda_torch_cmd = "pytorch torchvision torchaudio -c pytorch"
        else:
            print(">>> 推荐: PyTorch CPU 版本 (未检测到 NVIDIA GPU)")
            torch_pkgs = ['torch', 'torchvision', 'torchaudio']
            torch_extra_index = "https://download.pytorch.org/whl/cpu"
            conda_torch_cmd = "pytorch torchvision torchaudio cpuonly -c pytorch"
            
        pkgs_pip = torch_pkgs + pkgs_pip
        # Conda logic handled below
    
    # 1. Handle Target: New Conda Env
    if target == 'conda_new':
        if not env_name:
            env_name = f"env_{suite}_{int(time.time())}"
        print(f"正在创建新 Conda 环境: {env_name} ...")
        res = run_command(f"conda create -n {env_name} python=3.10 -y", stream_output=True, stop_event=stop_event)
        if res.returncode != 0: raise Exception("Conda create failed")
        
        # Install logic
        if suite == 'dl_torch':
            if stop_event and stop_event.is_set(): raise InterruptedError()
            # Install Torch first via Conda
            print(f"正在安装 PyTorch (Conda)...")
            res = run_command(f"conda install -n {env_name} -y {conda_torch_cmd}", stream_output=True, stop_event=stop_event)
            if res.returncode != 0: raise Exception("PyTorch install failed")

            if stop_event and stop_event.is_set(): raise InterruptedError()
            # Install rest via Pip (often faster/more compatible for misc libs)
            # Or install rest via Conda? Mixed is tricky. 
            # Let's try to install rest via Pip inside Conda to be safe with versions like opencv-python
            print(f"正在安装其他依赖 (Pip)...")
            pkgs_str = " ".join(pkgs_conda)
            # Use 'conda run' to ensure we use the env's pip
            cmd = f"conda run -n {env_name} pip install {pkgs_str} -i {mirror_url}"
            res = run_command(cmd, stream_output=True, stop_event=stop_event)
            if res.returncode != 0: raise Exception("Pip install failed")
        else:
            if stop_event and stop_event.is_set(): raise InterruptedError()
            # Generic Conda Install
            print(f"正在安装 Conda 包...")
            pkgs_str = " ".join(pkgs_conda)
            res = run_command(f"conda install -n {env_name} -y {pkgs_str} -c conda-forge", stream_output=True, stop_event=stop_event)
            if res.returncode != 0: raise Exception("Conda install failed")

        # Get env path for user reference
        env_path = "Unknown"
        try:
            # Fast way to get prefix
            p_res = run_command(f"conda run -n {env_name} python -c \"import sys; print(sys.prefix)\"", capture_output=True)
            if p_res and p_res.stdout:
                env_path = p_res.stdout.strip()
        except:
            pass

        return {"message": f"环境 {env_name} 创建并安装成功！\n位置: {env_path}", "env_name": env_name, "env_path": env_path, "type": "conda"}

    # 2. Handle Target: Current Conda Env
    elif target == 'conda_current':
        if suite == 'dl_torch':
             print(f"正在当前环境安装 PyTorch (Conda)...")
             res = run_command(f"conda install -y {conda_torch_cmd}", stream_output=True, stop_event=stop_event)
             if res.returncode != 0: raise Exception("PyTorch install failed")
             
             if stop_event and stop_event.is_set(): raise InterruptedError()
             print(f"正在安装其他依赖 (Pip)...")
             pkgs_str = " ".join(pkgs_conda)
             # Assume 'pip' is in path
             res = run_command(f"pip install {pkgs_str} -i {mirror_url}", stream_output=True, stop_event=stop_event)
             if res.returncode != 0: raise Exception("Pip install failed")
        else:
             print(f"正在当前 Conda 环境安装...")
             pkgs_str = " ".join(pkgs_conda)
             res = run_command(f"conda install -y {pkgs_str} -c conda-forge", stream_output=True, stop_event=stop_event)
             if res.returncode != 0: raise Exception("Conda install failed")
        return {"message": "当前 Conda 环境安装成功！", "type": "conda_existing"}

    # 3. Handle Target: Current Pip (Global/User)
    elif target == 'pip_current':
        print(f"正在使用 Pip 安装 ({len(pkgs_pip)}个)...")
        
        # Install generic packages first
        # Filter out torch pkgs if we need special index
        if suite == 'dl_torch':
            generic_pkgs = [p for p in pkgs_pip if p not in ['torch', 'torchvision', 'torchaudio']]
            torch_related = ['torch', 'torchvision', 'torchaudio']
            
            # 1. Install Generic
            if generic_pkgs:
                pkgs_str = " ".join(generic_pkgs)
                cmd = f"\"{sys.executable}\" -m pip install {pkgs_str} -i {mirror_url}"
                res = run_command(cmd, stream_output=True, stop_event=stop_event)
                if res.returncode != 0: raise Exception("Pip install failed")
            
            if stop_event and stop_event.is_set(): raise InterruptedError()

            # 2. Install Torch with Index
            print(f"正在安装 PyTorch ({torch_extra_index or 'Default Index'})...")
            
            cmd_parts = [f"\"{sys.executable}\"", "-m", "pip", "install"] + torch_related
            if torch_extra_index:
                cmd_parts += ["--index-url", torch_extra_index]
            else:
                cmd_parts += ["-i", mirror_url] # Use mirror if no special index needed (e.g. Mac)
            
            cmd = " ".join(cmd_parts)
            res = run_command(cmd, stream_output=True, stop_event=stop_event)
            if res.returncode != 0: raise Exception("PyTorch install failed")
            
        else:
            # Normal install
            pkgs_str = " ".join(pkgs_pip)
            cmd = f"\"{sys.executable}\" -m pip install {pkgs_str} -i {mirror_url}"
            res = run_command(cmd, stream_output=True, stop_event=stop_event)
            if res.returncode != 0: raise Exception("Pip install failed")
            
        return {"message": "Pip 安装成功！", "type": "pip"}

    else:
        raise ValueError("未知目标环境")

def quick_install_pkg(pkg, stop_event=None):
    """
    Quickly installs common packages using system pip or current env.
    For this demo, we'll just use the current python's pip but nicely formatted.
    Realistically, user wants a NEW env for this.
    """
    mirror_url = "https://pypi.tuna.tsinghua.edu.cn/simple"
    
    if pkg == "pytorch":
        print("正在安装 PyTorch (CPU版, 适合快速学习)...")
        cmd = f"\"{sys.executable}\" -m pip install torch torchvision torchaudio -i {mirror_url}"
        res = run_command(cmd, stream_output=True, stop_event=stop_event)
        if res.returncode != 0: raise Exception("PyTorch install failed")
        return {"message": "PyTorch 安装完成", "type": "pip"}
        
    elif pkg == "tensorflow":
        print("正在安装 TensorFlow...")
        cmd = f"\"{sys.executable}\" -m pip install tensorflow -i {mirror_url}"
        res = run_command(cmd, stream_output=True, stop_event=stop_event)
        if res.returncode != 0: raise Exception("TensorFlow install failed")
        return {"message": "TensorFlow 安装完成", "type": "pip"}
        
    elif pkg == "react":
        print("正在创建 React 项目 (create-react-app)...")
        # Check npm
        res = run_command("npm create vite@latest my-react-app -- --template react", stream_output=True, stop_event=stop_event)
        if res.returncode != 0: raise Exception("React init failed")
        return {"message": "React 项目模板已创建 (当前目录下 my-react-app)", "env_path": os.path.join(os.getcwd(), "my-react-app"), "type": "npm", "env_name": "my-react-app"}
        
    elif pkg == "vue":
        print("正在创建 Vue 项目...")
        res = run_command("npm create vite@latest my-vue-app -- --template vue", stream_output=True, stop_event=stop_event)
        if res.returncode != 0: raise Exception("Vue init failed")
        return {"message": "Vue 项目模板已创建 (当前目录下 my-vue-app)", "env_path": os.path.join(os.getcwd(), "my-vue-app"), "type": "npm", "env_name": "my-vue-app"}
        
    return {"message": "未知包", "type": "unknown"}
