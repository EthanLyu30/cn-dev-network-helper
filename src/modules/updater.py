import os
import json
import re
import subprocess
import urllib.request

_TAG_RE = re.compile(r"^v?(\d+(?:\.\d+){0,3}).*$")

def _get_repo_from_env():
    repo = os.environ.get("GITHUB_REPO") or os.environ.get("REPO") or ""
    repo = repo.strip()
    if "/" in repo and " " not in repo:
        return repo
    return None

def _get_repo_from_git_remote():
    try:
        res = subprocess.run(
            "git config --get remote.origin.url",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        if res.returncode != 0:
            return None
        url = (res.stdout or "").strip()
        if not url:
            return None
    except Exception:
        return None

    if url.startswith("git@github.com:"):
        slug = url[len("git@github.com:") :]
        if slug.endswith(".git"):
            slug = slug[:-4]
        return slug

    if "github.com/" in url:
        slug = url.split("github.com/")[-1]
        slug = slug.split("?")[0].split("#")[0]
        if slug.endswith(".git"):
            slug = slug[:-4]
        parts = [p for p in slug.split("/") if p]
        if len(parts) >= 2:
            return parts[0] + "/" + parts[1]
    return None

def get_repo_slug():
    return _get_repo_from_env() or _get_repo_from_git_remote()

def _parse_version(tag):
    tag = (tag or "").strip()
    m = _TAG_RE.match(tag)
    if not m:
        return None
    nums = m.group(1).split(".")
    try:
        return tuple(int(x) for x in nums)
    except Exception:
        return None

def _is_remote_newer(local_version, remote_tag):
    lv = _parse_version(local_version)
    rv = _parse_version(remote_tag)
    if not lv or not rv:
        return False
    max_len = max(len(lv), len(rv))
    lv2 = lv + (0,) * (max_len - len(lv))
    rv2 = rv + (0,) * (max_len - len(rv))
    return rv2 > lv2

def fetch_latest_release(repo_slug, timeout=3):
    url = f"https://api.github.com/repos/{repo_slug}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "network-booster"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {
        "tag_name": data.get("tag_name"),
        "html_url": data.get("html_url") or f"https://github.com/{repo_slug}/releases/latest",
        "name": data.get("name"),
    }

def check_for_updates(local_version, timeout=3):
    repo = get_repo_slug()
    if not repo:
        return None
    try:
        latest = fetch_latest_release(repo, timeout=timeout)
    except Exception:
        return None

    tag = latest.get("tag_name") or ""
    if not tag:
        return None

    available = _is_remote_newer(local_version, tag)
    return {
        "repo": repo,
        "local_version": local_version,
        "latest_tag": tag,
        "url": latest.get("html_url"),
        "available": available,
    }

