"""从 Cookie 字符串 / 浏览器导出的 cookies.txt 中取 Cookie。"""
from __future__ import annotations

import os
from pathlib import Path


def from_string(raw: str, domain: str = "") -> str:
    """把 "a=1; b=2" 规范化；如果传的是整段 Cookie 头也能用。"""
    raw = (raw or "").strip()
    if raw.lower().startswith("cookie:"):
        raw = raw.split(":", 1)[1]
    parts = []
    for chunk in raw.replace("\n", ";").split(";"):
        chunk = chunk.strip()
        if "=" in chunk:
            parts.append(chunk)
    return "; ".join(parts)


def from_netscape(path: str, domain: str = "") -> str:
    """解析 Netscape cookies.txt（Chrome/Firefox 导出插件通用格式）。"""
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(path)
    pairs, seen = [], set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or (line.startswith("#") and not line.startswith("#HttpOnly_")):
            continue
        line = line.removeprefix("#HttpOnly_")
        cols = line.split("\t")
        if len(cols) < 7:
            continue
        dom, _flag, _path, _secure, _exp, name, value = cols[:7]
        if domain and domain not in dom:
            continue
        if name in seen:
            continue
        seen.add(name)
        pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def resolve(cookie: str | None, cookie_file: str | None, provider: str, domain: str) -> str:
    """命令行 > provider 环境变量 > 通用环境变量。"""
    if cookie:
        return from_string(cookie, domain)
    if cookie_file:
        return from_netscape(cookie_file, domain)
    env_keys = {f"{provider.upper()}_COOKIE", "CN_JOBS_COOKIE"}
    for key in env_keys:
        val = os.environ.get(key)
        if val:
            return from_string(val, domain)
    return ""
