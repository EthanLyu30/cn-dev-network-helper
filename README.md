# 🇨🇳 全能开发环境网络配置助手 (All-in-One Network Booster)

> **一句话介绍**：专为中国开发者打造的“网络加速瑞士军刀”，一键解决 Git、Pip、Conda、Node、Go、Docker 等工具的连接超时与卡顿问题。

---

## 🎯 为什么你需要这个项目？

在国内进行软件开发，你是否经常遇到以下崩溃瞬间：

*   🤬 **Git Clone/Push/Push** 速度只有几 KB/s，或者直接 `Connection time` / `443d 错误 out` / `443` 错误。
*   🐢 **Pip Install** 下载到 99% 突然断开，且没有断点续传。
*   🌀 **Conda** 解析依赖转圈圈半小时，最后报错。
*   🤯 **手动配置繁琐**：既要记 VPN 端口，又要记各种镜像源地址，还得来回切换（内网/外网冲突）。

**核心策略 (The Solution)**：
*   **Git**: 采用 **智能分流代理**。仅 `github.com` 走本地代理，Gitee/GitLab/公司内网依然直连。
*   **Pip / Conda / Node**: 优先使用 **国内高速镜像** (清华/阿里/腾讯)，解决 99% 的下载问题；特殊情况（缺包）提供一键切换 **官方源+代理** 模式。

---

## 🚀 快速开始 (Quick Start)

本项目已实现 **零依赖**，仅需 Python (3.6+) 即可运行。

### 1. 启动工具

推荐使用 **Web 可视化界面**，操作更直观：

```bash
# 启动 Web 界面 (推荐)
python main.py --web

# 或者使用 命令行菜单 (CLI)
python main.py
```

### 2. 功能演示

*   **智能推荐**: 点击“一键检测”，脚本会自动扫描你的 VPN 端口，并同时测试“直连镜像”与“代理官方源”的延迟，告诉你当前最快的方案。
*   **一键配置**: 选择方案后，自动修改 `.gitconfig`, `pip.ini`, `.condarc` 等配置文件。
*   **安全无忧**: 每次修改前，系统会自动备份旧配置到 `.backup/` 目录，随时可以“一键还原”。

---

## ✨ 核心功能矩阵 (Features)

| 工具 (Tool) | 镜像模式 (Mirror) | 代理模式 (Proxy) | 智能特性 (Smart) |
| :--- | :--- | :--- | :--- |
| **Git** | - | ✅ (智能分流) | 仅 GitHub 走代理，内网直连 |
| **Python** (Pip) | ✅ (清华/阿里) | ✅ | 智能安装 `requirements.txt` (失败自动切代理) |
| **Conda** | ✅ (清华/北外) | ✅ | 自动清理旧源，解决 SAT 求解慢 |
| **Node.js** | ✅ (淘宝/腾讯) | ✅ | 支持 npm / yarn / pnpm |
| **Go** | ✅ (七牛/阿里) | - | 设置 GOPROXY |
| **Docker** | ✅ (多源加速) | - | 自动配置 `daemon.json` |

---

## 📖 手动配置指南 (Manual Configuration)

如果你更喜欢手动掌控一切，或者想了解脚本背后的原理，这里是核心配置代码：

### 1. Git 智能分流 (仅 GitHub 走代理)
大多数 Git 卡顿是因为 `github.com` 连接慢。直接设置全局代理会影响内网访问。
**原理**：利用 Git 的 `http.<url>.proxy` 功能，实现精准代理。

```bash
# 假设你的代理端口是 7897 (请根据实际情况修改)
git config --global http.https://github.com.proxy http://127.0.0.1:7897

# 还原 (取消代理)
git config --global --unset http.https://github.com.proxy
```

### 2. Pip 加速 (镜像 vs 代理)
*   **镜像模式 (推荐)**：
    ```bash
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    ```
*   **代理模式 (救急用)**：
    ```bash
    # 临时使用
    pip install package_name --proxy http://127.0.0.1:7897
    ```

### 3. Conda 加速
修改用户目录下的 `.condarc` 文件：
```yaml
# 镜像模式配置示例
channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
show_channel_urls: true
```

---

## 📂 项目结构 (Structure)

模块化设计，清晰易懂：

```text
git_pip_conda_connectionfailure_research/
├── main.py                 # 🚀 程序入口 (启动 CLI 或 Web)
├── README.md               # 📄 说明文档
├── src/
│   ├── core/               # 🧠 核心逻辑
│   │   ├── utils.py        # 工具箱 (端口检测、测速、注册表读取)
│   │   └── backup.py       # 安全保障 (配置备份与还原)
│   ├── modules/            # 🔧 各工具独立模块
│   │   ├── git.py          # Git 智能配置
│   │   ├── python.py       # Pip/Conda 配置
│   │   ├── node.py         # Node.js 全家桶配置
│   │   ├── docker.py       # Docker 镜像加速
│   │   └── go.py           # Go Proxy 配置
│   └── web/                # 🌐 Web 界面模块
│       ├── server.py       # 轻量级 HTTP 后端
│       └── static/         # 前端资源
└── .backup/                # 📦 自动生成的备份目录
```

---

## ❓ 常见问题 (FAQ)

### Q1: 为什么 Git Push 经常报 443 错误？
A: 这通常是因为 DNS 污染或连接不稳定。使用本工具的 **Git 智能代理模式** 可以强制 Git 流量走 VPN 通道，通常能完美解决此问题。

### Q2: 为什么 Pip 比 Conda 快？
A: Pip 的依赖解析相对简单，且 Wheel 包体积小。Conda 需要进行复杂的 SAT 求解（确保 C++/CUDA 库兼容），且元数据庞大。建议：**能用 Pip 解决的先用 Pip，科学计算库再用 Conda**。

### Q3: 报错 SSL Error 怎么办？
A: 这通常是代理软件拦截了 SSL 证书。
*   **临时方案**：关闭 VPN 的“系统代理”模式，仅保留 TUN 或手动端口代理。
*   **Git**: `git config --global http.sslVerify false` (不推荐长期使用)。

---

## 🧠 核心原理 (How it works)

1.  **🕵️ 自动侦探 (Auto-Detection)**:
    *   不再需要手动输入端口！脚本会自动读取 Windows 注册表或扫描常用端口 (7890, 7897, 1080 等) 来发现你的 VPN 代理。
2.  **🏇 赛马机制 (Speed Racing)**:
    *   脚本会实时发起网络请求，同时测试 **[直连清华源]** 和 **[代理连官方源]** 的延迟，用数据说话，推荐最快路径。
3.  **🛡️ 容错兜底**:
    *   Pip 安装失败了？脚本会捕捉错误，并建议你“是否切换代理重试？”，专治各种包不存在或哈希不匹配。

---

## 📜 更新日志 (Changelog)

### v3.0 (Current) - 全能进化
*   **重构**: 采用模块化架构，代码更清晰，易于扩展。
*   **新增**: Web 可视化界面 (无依赖)。
*   **扩展**: 新增 Node.js (npm/yarn/pnpm), Go, Docker 支持。
*   **安全**: 引入自动备份 (Backup) 与一键还原功能。

### v2.0 - 智能化
*   **特性**: 引入“自动端口检测”和“赛马测速”机制。
*   **优化**: Git 配置升级为智能分流模式。

### v1.0 - 雏形
*   **基础**: 提供简单的 Git 和 Pip 代理设置脚本。

---

## 🔮 未来规划 (Roadmap)

我们致力于解决开发环境的“最后一公里”问题：

*   [ ] **macOS/Linux 深度适配**: 优化非 Windows 环境下的端口检测机制。
*   **GitHub Hosts**: 集成 GitHub Hosts 自动更新功能，作为代理失效时的备选方案。
*   **系统级代理**: 提供一键设置终端 (Terminal) 临时代理的功能 (`export http_proxy=...`)。
*   **局域网共享**: 允许局域网内其他机器通过本机代理上网。

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 PR！让我们一起改善国内开发者的网络体验。
