# 🇨🇳 全能开发环境网络配置助手 (All-in-One Network Booster)

> **一句话介绍**：专为中国开发者打造的“网络加速瑞士军刀”，一键解决 Git、Pip、Conda、Node、Go、Docker 等工具的连接超时与卡顿问题。

---

## 🎯 为什么你需要这个项目？

在国内进行软件开发，你是否经常遇到以下崩溃瞬间：

*   🤬 **Git Clone/Push** 速度只有几 KB/s，或者直接 `Connection time`  / `443` 错误。
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

### 4. 局域网共享 (手机/其他设备)
适用于：你的电脑开着代理软件，想让手机、平板、虚拟机、局域网内另一台电脑也共享这条代理链路。

1. **在电脑代理软件中开启 Allow LAN**
    - Clash / v2rayN / v2rayA 等通常都有 “允许来自局域网的连接 (Allow LAN)” 选项
2. **确认本机局域网 IP 与端口**
    - Windows: `ipconfig` 查看 `IPv4 地址`，形如 `192.168.x.x`
    - macOS/Linux: `ifconfig` 或 `ip a`
    - 端口：例如 `7890` / `7897`（可用本工具自动检测）
3. **在手机上设置 Wi‑Fi 代理**
    - 确保手机与电脑连接同一个 Wi‑Fi
    - Wi‑Fi 设置 → 当前 Wi‑Fi → 代理(Proxy) → 手动(Manual)
    - Host 填写电脑的 `192.168.x.x`，Port 填写代理端口（如 `7897`）
4. **常见坑**
    - 电脑防火墙阻止入站端口：需要放行该端口的入站规则
    - 代理软件只监听 `127.0.0.1`：需要改为监听 `0.0.0.0` 或开启局域网监听

---

## 📂 项目结构 (Structure)

模块化设计，清晰易懂：

```text
git_pip_conda_connectionfailure_research/
├── main.py                 # 🚀 程序入口 (启动 CLI 或 Web)
├── setup_network.py        # 🕰️ 历史遗留版本 (Legacy 单文件版，不再维护)
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
│   │   ├── go.py           # Go Proxy 配置
│   │   ├── hosts.py        # GitHub Hosts 更新
│   │   └── proxy_tools.py  # 终端代理/局域网共享工具
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

### Q4: 什么是 GitHub Hosts 更新？为什么需要它？
A: 当代理软件也无法解决 GitHub 访问问题时（通常因为 DNS 污染导致域名解析到错误的 IP），直接修改系统的 `/etc/hosts` 文件，将 GitHub 域名强制指向已知的可用 IP 是一种有效手段。本工具集成了 GitHub520 项目，一键获取最新 IP 并写入 Hosts。

### Q5: 手机连电脑代理后，小红书提示网络不好，但其他 App 正常？
A: 这种情况非常常见，核心原因是：你用的是“Wi‑Fi HTTP 代理”，而电脑的代理软件如果处于“全局走 VPN 出口”，小红书访问国内 CDN/风控节点时会遇到高延迟、出口异常或风控策略，从而提示网络不好。

推荐解决方案（手机无 VPN 的前提下）：
1. **电脑代理软件切换规则模式 (Rule/绕过中国大陆)**：让国内流量直连、仅国外走代理，这样小红书走国内直连链路。
2. **为小红书域名加直连规则 (DIRECT)**：例如 `xiaohongshu.com`、`xhscdn.com`、`xhslink.com` 等强制直连（具体域名可按抓包/日志补齐）。
3. **检查代理监听与防火墙**：确保已开启 Allow LAN，且代理监听不只在 `127.0.0.1`，否则会出现“部分请求直连失败/回落异常”。

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

### v3.5 (Latest) - Web UI 体验增强
*   **真实进度与日志**: Web UI 统一使用 SSE 展示真实进度、操作日志与失败原因提示。
*   **诊断报告导出**: Web UI 支持导出诊断报告（JSON）。
*   **Hosts 写入体验**: 增加管理员权限检测与“一键管理员重启 Web（写 Hosts）”。

### v3.4 - Web 工具箱
*   **Web 工具箱**: 增加 Hosts 更新/终端代理/局域网共享向导，并统一纳入 SSE 日志与诊断报告导出。

### v3.3 - 体验增强
*   **Web 进度**: Web 界面增加进度条与预计耗时提示。
*   **文档**: 补充局域网共享（手机/其他设备）详细说明。

### v3.2 - 工具箱增强
*   **终端代理**: 新增“一键获取终端代理命令”功能，支持 PowerShell/CMD/Bash。
*   **局域网共享**: 新增局域网代理共享指南，帮助同一局域网下的设备（如手机、虚拟机）共享主机代理。
*   **Hosts 更新**: 集成 GitHub520 实时 Hosts 更新，对抗 DNS 污染。

### v3.1 - 跨平台与稳定性
*   **兼容**: 增强 macOS/Linux 支持，新增环境变量端口检测。
*   **诊断**: 增强 Git 连接诊断工具。

### v3.0 - 全能进化
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

已完成的里程碑请查看上方更新日志，Roadmap 仅保留待做事项。

### v4.0 (Next)
*   [ ] **一键环境初始化**: 支持模板化配置 (Deep Learning, Web Dev 等)。
*   [ ] **插件系统**: 允许用户编写自定义 Python 脚本来扩展功能。
*   [ ] **自动更新**: 启动时检查 Release 并提示更新。

### v4.x (Later)
*   [ ] **局域网共享向导**: 自动检测 Allow LAN/监听地址/防火墙放行，并给出修复建议。
*   [ ] **智能策略升级**: 基于历史测速缓存与失败回退，降低反复测速与误判。
*   [ ] **局域网多机下发**: 同一局域网内一键将配置下发到其他设备 (可选)。

---

## 🤝 贡献与反馈

欢迎提交 Issue 或 PR！让我们一起改善国内开发者的网络体验。
