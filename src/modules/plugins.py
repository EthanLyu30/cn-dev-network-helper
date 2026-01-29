import os
import re
import runpy
import json
from ..core.utils import Colors

_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")

def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def get_plugins_dir():
    return os.path.join(_repo_root(), "plugins")

def list_plugins():
    plugins_dir = get_plugins_dir()
    if not os.path.isdir(plugins_dir):
        return []

    items = []
    for name in sorted(os.listdir(plugins_dir)):
        if not name.endswith(".py"):
            continue
        if not _NAME_RE.match(name):
            continue
        path = os.path.join(plugins_dir, name)
        items.append({"name": name, "path": path})
    return items

def run_plugin(plugin_name, context):
    if not plugin_name:
        raise ValueError("missing plugin name")
    if not _NAME_RE.match(plugin_name):
        raise ValueError("invalid plugin name")

    if not plugin_name.endswith(".py"):
        plugin_name = plugin_name + ".py"

    plugins_dir = get_plugins_dir()
    path = os.path.join(plugins_dir, plugin_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"plugin not found: {plugin_name}")

    ctx = context or {}
    os.environ["PLUGIN_CONTEXT_JSON"] = json.dumps(ctx, ensure_ascii=False)
    Colors.print_info(f"正在运行插件: {plugin_name}")
    ns = runpy.run_path(path, init_globals={"CONTEXT": ctx})
    result = ns.get("RESULT")
    if result is not None:
        return result
    return {"message": "plugin finished"}

