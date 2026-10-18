"""适配器注册表。新增站点时：写一个模块，实现 search()/detail()，然后加到这里。"""
from __future__ import annotations

from . import boss, demo

REGISTRY = {
    "boss": boss,
    "demo": demo,
}

_META = {
    "boss": {
        "status": "live",
        "site": "https://www.zhipin.com",
        "needs_cookie": True,
        "note": "国内最大互联网招聘平台；风控强，数据中心/海外 IP 会返回 code=37",
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
