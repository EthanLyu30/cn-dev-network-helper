from ..core.utils import detect_proxy_port, Colors
from .python import set_pip_mirror, set_pip_proxy, set_conda_mirror, set_conda_proxy
from .node import set_node_mirror, set_node_proxy
from .git import set_git_proxy
from .go import set_go_proxy
from .docker import set_docker_mirror

TEMPLATES = {
    "deep_learning": {
        "label": "Deep Learning",
        "description": "Python/Conda + Docker + GitHub 加速（偏科学计算/镜像）",
        "steps": [
            ("python", "mirror"),
            ("docker", "mirror"),
            ("git", "proxy"),
            ("go", "mirror"),
        ],
    },
    "web_dev": {
        "label": "Web Dev",
        "description": "Node + Python + GitHub 加速（偏前端/镜像）",
        "steps": [
            ("node", "mirror"),
            ("python", "mirror"),
            ("git", "proxy"),
            ("go", "mirror"),
        ],
    },
}

def _describe_step(module, mode):
    if module == "python" and mode == "mirror":
        return "Python: Pip/Conda 镜像模式（清华等）"
    if module == "python" and mode == "proxy":
        return "Python: Pip/Conda 代理模式（官方源 + 本地代理）"
    if module == "node" and mode == "mirror":
        return "Node: npm/yarn/pnpm 镜像模式（npmmirror 等）"
    if module == "node" and mode == "proxy":
        return "Node: npm/yarn/pnpm 代理模式（本地代理）"
    if module == "git":
        return "Git: 仅 GitHub 走智能分流代理"
    if module == "go":
        return "Go: 设置 GOPROXY（国内加速）"
    if module == "docker":
        return "Docker: 设置镜像加速（daemon.json）"
    return f"{module}: {mode}"

def list_templates():
    items = []
    for key, meta in TEMPLATES.items():
        steps = meta.get("steps") or []
        items.append(
            {
                "key": key,
                "label": meta.get("label") or key,
                "description": meta.get("description") or "",
                "steps": [{"module": m, "mode": md, "label": _describe_step(m, md)} for m, md in steps],
            }
        )
    return sorted(items, key=lambda x: x["key"])

def apply_template(template_key, port=None, mode=None):
    if template_key not in TEMPLATES:
        raise ValueError("unknown template")

    meta = TEMPLATES[template_key]
    steps = meta.get("steps") or []
    mode = (mode or "").strip().lower() or None
    if not port:
        port = detect_proxy_port()

    applied = []
    for module, default_mode in steps:
        step_mode = mode or default_mode
        Colors.print_info(f"模板步骤: {module} ({step_mode})")

        if module == "python":
            if step_mode == "mirror":
                set_pip_mirror()
                set_conda_mirror()
            elif step_mode == "proxy":
                set_pip_proxy(port)
                set_conda_proxy(port)
            else:
                raise ValueError("unknown python mode")
            applied.append({"module": "python", "mode": step_mode})
            continue

        if module == "node":
            if step_mode == "mirror":
                set_node_mirror()
            elif step_mode == "proxy":
                set_node_proxy(port)
            else:
                raise ValueError("unknown node mode")
            applied.append({"module": "node", "mode": step_mode})
            continue

        if module == "git":
            set_git_proxy(port)
            applied.append({"module": "git", "mode": "proxy"})
            continue

        if module == "go":
            set_go_proxy()
            applied.append({"module": "go", "mode": "mirror"})
            continue

        if module == "docker":
            set_docker_mirror()
            applied.append({"module": "docker", "mode": "mirror"})
            continue

        raise ValueError("unknown module")

    return {
        "template": template_key,
        "label": meta.get("label") or template_key,
        "description": meta.get("description") or "",
        "port": str(port) if port is not None else None,
        "applied": applied,
    }
