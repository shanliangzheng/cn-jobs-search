"""适配器注册表。新增站点时：写一个模块，实现 search()/detail()，然后加到这里。"""
from __future__ import annotations

from . import boss, demo, liepin

REGISTRY = {
    "boss": boss,
    "demo": demo,
    "liepin": liepin,
}

_META = {
    "boss": {
        "status": "live",
        "site": "https://www.zhipin.com",
        "needs_cookie": True,
        "note": "国内最大互联网招聘平台；风控强，数据中心/海外 IP 会返回 code=37",
    },
    "liepin": {
        "status": "experimental",
        "site": "https://www.liepin.com",
        "needs_cookie": True,
        "note": "接口按公开资料实现，未在真实网络验证；用 --raw 保存响应可离线校准",
    },
    "demo": {
        "status": "offline",
        "site": "本地 fixtures",
        "needs_cookie": False,
        "note": "内置 6 条样例，用于跑通 search → detail → /apply",
    },
}


def describe() -> list[dict]:
    return [{"name": k, **_META.get(k, {})} for k in sorted(REGISTRY)]
