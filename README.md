# 🇨🇳 中国开发者网络环境配置指南 (Git/Pip/Conda)

本项目旨在解决国内开发者在使用 `git`、`pip`、`conda` 时常遇到的卡顿、连接超时等问题。核心策略是：**Git 走智能代理，Pip/Conda 走国内镜像**。

## 🚨 核心排查原则
**发现问题先定性**：
1. **配置是否生效？** (检查 config)
2. **代理节点是否通畅？** (检查梯子本身)

> **实战教训**：如果配置了代理后突然全网断联，通常是因为**代理节点本身挂了或延迟过高**，而非配置错误。此时应切换低延迟节点，而非盲目删除配置。

---

## 🚀 一键配置脚本 (v2.2 全能版)

为了最大化解决“环境配置”这个痛点，我把脚本升级成了**全能助手**。它不仅能配置环境，还能帮你**智能安装依赖**和**诊断 Git 卡顿**。

### 脚本核心逻辑说明
这个脚本 (`setup_network.py`) 的工作原理非常简单直接：
1.  **自动侦探**：它会自动扫描你的系统注册表或常用端口 (7890/7897 等)，找到你的 VPN/代理端口。
2.  **赛马机制**：它会同时测试“直连清华源”和“VPN 连官方源”的速度，谁快就用谁。
3.  **智能决策**：
    *   **镜像模式** (默认)：配置 pip/conda 使用国内清华源，速度最快。
    *   **代理模式 (VPN)**：配置 pip/conda 走本地代理，专门解决“国内源缺包”的问题。

### 新增功能 (针对你的需求)
1.  **智能安装 requirements.txt** (菜单选项 6)
    *   **痛点**：有时候用国内源装了一半报错说“找不到包”，还得手动切 VPN 重试。
    *   **解决**：脚本会自动先尝试用**清华源**极速安装；如果失败，它会提示你是否切换到**VPN 代理模式**重试。你只需要准备好 `requirements.txt`，剩下的交给脚本。

2.  **Git 连接专项诊断** (菜单选项 7)
    *   **痛点**：不知道为什么 Git push 突然卡顿。
    *   **解决**：脚本会专门测试 GitHub 的直连延迟 vs 代理延迟。如果发现直连超时而代理很快，它会**强烈建议**你开启 Git 智能代理，并支持一键修复。

### 使用方法
```bash
python setup_network.py
```
*   选 `1`: 自动测速并推荐最佳全局配置。
*   选 `6`: 帮你装 `requirements.txt` (最快路径)。
*   选 `7`: 看看你的 Git 为什么卡，并一键修好。

---

## 1. Git 配置：智能分流 (强烈推荐)

大多数 Git 卡顿是因为连接 `github.com` 慢。直接设置全局代理会影响 Gitee 或公司内网 GitLab 的访问。
**解决方案**：仅针对 GitHub 开启代理。

### ✅ 推荐配置 (智能分流)
假设你的本地代理端口是 `7897` (请根据你的代理软件实际端口修改，常见有 7890, 1080 等)：

```bash
# 仅对 github.com 设置代理 (Windows/Mac/Linux 通用)
git config --global http.https://github.com.proxy http://127.0.0.1:7897

# 验证配置
git config --global --get-regexp http.*
# 应输出：http.https://github.com.proxy http://127.0.0.1:7897
```

### 效果
- **GitHub** (`https://github.com/...`) -> **走代理** (极速)
- **Gitee/GitLab/其他** -> **直连** (不影响内网速度)

### 常用命令备忘
```bash
# 查看当前代理配置
git config --global --get http.proxy
git config --global --get https.proxy

# 删除旧的全局强制代理 (如果你之前设置过)
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 2. Pip 配置：国内镜像源

Pip 不需要走代理，使用国内镜像源速度更快且稳定。

### ✅ 推荐配置 (清华源/阿里云)

**临时使用**：
```bash
pip install some-package -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**永久配置 (推荐)**：
```bash
# 设置清华源为默认
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 或者使用阿里云
# pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

**验证**：
```bash
pip config list
```

---

## 3. Conda 配置：国内镜像源

Conda 的包体积通常较大，强烈建议配置镜像。

### ✅ 推荐配置 (清华源/北外源)

修改用户目录下的 `.condarc` 文件，或使用命令：

```bash
# 1. 生成 .condarc 文件 (如果不存在)
conda config --set show_channel_urls yes

# 2. 添加清华源 (Tsinghua)
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch/

# 3. 设置搜索时显示通道地址
conda config --set show_channel_urls yes
```

**注意**：如果遇到镜像源连接错误 (SSL Error)，可能需要暂时关闭代理软件的“系统代理”模式，或者在 `.condarc` 中添加 `ssl_verify: false` (不推荐，仅作为临时方案)。

---

## 4. 常见问题 FAQ

### Q1: 配置了 Git 代理还是连不上？
1. **检查端口**：确认你的代理软件端口是 `7897` 还是 `7890`？(查看代理软件设置 -> 本地端口)
2. **检查协议**：Git 配置中通常使用 `http://` 前缀指向本地代理，即使代理软件支持 socks5。
3. **检查节点**：**这很重要！** 尝试在浏览器打开 GitHub，如果浏览器也打不开，说明你的代理节点挂了，切换节点即可，不要乱改配置。

### Q2: 为什么开着 VPN，Pip 还是慢？
Pip 默认走系统网络，有些 VPN 开启“全局模式”可能会接管 Pip 流量，但绕路国外反而慢。使用**国内镜像源**是 Pip 加速的终极方案，通常不需要 VPN。

### Q3: 为什么 Pip 通常比 Conda 快？(原理分析)
这是一个非常经典的问题，主要由两者机制决定：
1.  **依赖解析复杂度**：
    *   **Pip**：主要管理 Python 包。虽然现在也有依赖解析，但相对简单。
    *   **Conda**：是通用包管理器（包含 Python, C++, R, CUDA 等）。它必须确保所有二进制库（如 numpy 依赖的 MKL/OpenBLAS）与系统环境严格兼容。这需要求解一个巨大的 SAT（布尔可满足性）问题，**"转圈圈"通常是在解方程，而不是在下载**。
2.  **元数据体积**：Conda 的 repodata（索引文件）非常大（几百 MB），每次安装都要下载或检查索引更新，而 Pip 的索引请求非常轻量。
3.  **包内容**：Conda 包通常包含完整的独立运行环境（包括编译器、动态库），体积比 Pip 的 Wheel 包大得多。

### Q4: 报错 `OpenSSL.SSL.Error` 或 `SSLError`？
这通常是因为代理软件对 SSL 证书进行了拦截或干扰。
- **Git**: 尝试 `git config --global http.sslVerify false` (仅限临时解决)
- **Conda/Pip**: 检查是否开启了 VPN 的“TUN模式”或“系统代理”，尝试暂时关闭 VPN 使用镜像源直连。

---

## 5. 进阶：Pip/Conda 也可以像 Git 一样走代理

如果你**必须**访问官方源（例如某些包国内镜像还没同步，或者你在国外服务器上），你可以像配置 Git 一样配置代理。

### Pip 代理配置
Pip 不支持 Git 那种 `http.<domain>.proxy` 的精细分流，但可以设置全局代理。

**临时命令 (推荐)**：
```bash
# 假设代理端口为 7897
pip install package_name --proxy http://127.0.0.1:7897
```

**永久配置**：
```bash
# 在 pip.ini (Windows) 或 pip.conf (Mac/Linux) 中添加
[global]
proxy = http://127.0.0.1:7897
```

### Conda 代理配置
Conda 支持在 `.condarc` 中配置代理服务器。

**修改 `.condarc` 文件**：
```yaml
proxy_servers:
  http: http://127.0.0.1:7897
  https: http://127.0.0.1:7897
```

> **注意**：配置代理后，请确保你的 `channels` 恢复为 `defaults` (官方源)，因为国内镜像源通常拒绝国外代理 IP 访问。

