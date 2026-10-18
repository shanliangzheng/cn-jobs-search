"""BOSS 直聘（zhipin.com）适配器。

接口来自站点自身的 Web 端（非官方公开 API）：
  GET /wapi/zpgeek/search/joblist.json?scene=1&query=...&city=...&page=1
  GET /wapi/zpgeek/job/detail.json?securityId=...

注意：BOSS 风控很严，数据中心/海外 IP 基本会拿到 code=37「您的环境存在异常」。
在本机、浏览器已登录的前提下，把 Cookie（尤其 __zp_stoken__）传给 CLI 才能稳定取数。
"""
from __future__ import annotations

import json
import re
import urllib.parse
from datetime import datetime, timezone

from base import norm_job, strip_html
from net import FetchError, get_json

BASE = "https://www.zhipin.com"
SEARCH_URL = BASE + "/wapi/zpgeek/search/joblist.json"
DETAIL_URL = BASE + "/wapi/zpgeek/job/detail.json"

CODE_HINTS = {
    37: ("BLOCKED", "BOSS 返回 code=37（环境异常/风控）",
         "在浏览器登录后复制 Cookie（需要 __zp_stoken__），或换家庭宽带网络；降低请求频率"),
    1: ("AUTH_REQUIRED", "BOSS 要求登录", "传 --cookie 或在 BOSS_COOKIE 环境变量里放登录 Cookie"),
    7: ("AUTH_REQUIRED", "BOSS 要求登录", "传 --cookie 或在 BOSS_COOKIE 环境变量里放登录 Cookie"),
    17: ("BLOCKED", "请求过于频繁", "调大 --sleep，或过几分钟再试"),
    101: ("AUTH_REQUIRED", "需要完成安全验证", "浏览器里过一次验证后重新导出 Cookie"),
}


def _headers(cookie: str) -> dict:
    h = {
        "Referer": BASE + "/web/geek/job",
        "Origin": BASE,
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        h["Cookie"] = cookie
    return h


def _check(payload: dict) -> dict:
    code = payload.get("code", 0)
    if code == 0:
        return payload.get("zpData") or {}
    kind, msg, hint = CODE_HINTS.get(code, ("API_ERROR", f"BOSS 返回 code={code}", ""))
    detail = payload.get("message") or ""
    raise FetchError(kind, f"{msg}：{detail}".strip("："), hint=hint)


def _ts(value) -> str:
    """BOSS 的 lastModifyTime 是毫秒时间戳。"""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return ""
    if n > 10_000_000_000:
        n //= 1000
    return datetime.fromtimestamp(n, tz=timezone.utc).astimezone().strftime("%Y-%m-%d")


def _job_from_item(it: dict) -> dict:
    tags = list(dict.fromkeys([*(it.get("jobLabels") or []), *(it.get("skills") or [])]))
    jid = it.get("encryptJobId") or it.get("securityId") or ""
    return norm_job(
        source="boss",
        job_id=jid,
        title=it.get("jobName", ""),
        company=it.get("brandName", ""),
        salary=it.get("salaryDesc", ""),
        city=it.get("cityName", ""),
        district="·".join(x for x in [it.get("areaDistrict"), it.get("businessDistrict")] if x),
        experience=it.get("jobExperience", ""),
        degree=it.get("jobDegree", ""),
        tags=tags,
        url=f"{BASE}/job_detail/{jid}.html" if jid else "",
        boss=" ".join(x for x in [it.get("bossName"), it.get("bossTitle")] if x),
        industry=it.get("brandIndustry", ""),
        size=it.get("brandScaleName", ""),
        posted_at=_ts(it.get("lastModifyTime")),
    )


def search(query: str, city_code: str, page: int = 1, page_size: int = 30,
           cookie: str = "", timeout: float = 20, city_name: str = "",
           extra_params: dict | None = None,
           raw_file: str | None = None, debug: bool = False) -> list[dict]:
    params = {
        "scene": "1",
        "query": query,
        "city": city_code,
        "page": str(page),
        "pageSize": str(page_size),
    }
    if extra_params:
        params.update({k: str(v) for k, v in extra_params.items()})

    if raw_file:
        with open(raw_file, encoding="utf-8") as f:
            payload = json.load(f)
    else:
        url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
        payload = get_json(url, headers=_headers(cookie), timeout=timeout, debug=debug)

    data = _check(payload)
    items = data.get("jobList") or []
    jobs = [_job_from_item(it) for it in items]
    return [j for j in jobs if j["title"] or j["company"]]


def _security_id(value: str) -> str:
    v = value.strip()
    if v.startswith("http"):
        m = re.search(r"[?&]securityId=([^&#]+)", v)
        if m:
            return urllib.parse.unquote(m.group(1))
        raise FetchError("PARAM", "URL 里没有 securityId",
                         hint="请传 search 结果里的 ID/链接（形如 ...?securityId=xxx）")
    return v


def detail(job_id_or_url: str, cookie: str = "", timeout: float = 20,
           raw_file: str | None = None, debug: bool = False) -> dict:
    sid = _security_id(job_id_or_url)
    if raw_file:
        with open(raw_file, encoding="utf-8") as f:
            payload = json.load(f)
    else:
        url = DETAIL_URL + "?" + urllib.parse.urlencode({"securityId": sid})
        payload = get_json(url, headers=_headers(cookie), timeout=timeout, debug=debug)

    data = _check(payload)
    info = data.get("jobInfo") or {}
    brand = data.get("brandInfo") or {}
    boss = data.get("bossInfo") or {}

    desc = strip_html(info.get("jobDescription") or info.get("jobDesc") or "")
    tags = list(dict.fromkeys([*(info.get("jobLabels") or []), *(info.get("skills") or [])]))
    jid = info.get("encryptJobId") or sid

    return norm_job(
        source="boss",
        job_id=jid,
        title=info.get("jobName", ""),
        company=brand.get("brandName") or data.get("brandName", ""),
        salary=info.get("salaryDesc", ""),
        city=info.get("cityName", ""),
        district="·".join(x for x in [info.get("areaDistrict"), info.get("businessDistrict")] if x),
        experience=info.get("experienceName", ""),
        degree=info.get("degreeName", ""),
        tags=tags,
        url=f"{BASE}/job_detail/{jid}.html" if jid else "",
        description=desc,
        boss=" ".join(x for x in [boss.get("name"), boss.get("title")] if x),
        industry=brand.get("brandIndustry", ""),
        size=brand.get("brandScaleName", ""),
    )


def url_for(job: dict) -> str:
    return job.get("url") or ""
