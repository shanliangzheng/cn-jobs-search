"""猎聘（liepin.com）适配器 —— experimental。

接口与字段按 2026 年公开资料实现，但未能在真实网络验证（站点对数据中心 IP 有 WAF）。
用 --raw 保存真实响应即可离线校准；字段缺失时应优先修这里，而不是改上层。

搜索：POST https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job
详情：GET  https://www.liepin.com/job/<id>.shtml  → 解析 JSON-LD（schema.org JobPosting）
"""
from __future__ import annotations

import json
import re
import urllib.parse
import uuid

from base import norm_job, strip_html
from net import FetchError, post_json, request

BASE = "https://www.liepin.com"
SEARCH_API = "https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job"

# 猎聘自己的城市编码（dq），与 BOSS 不同；未收录的城市传空，由接口给全国结果
CITY_CODES = {
    "北京": "010", "上海": "020", "天津": "030020", "重庆": "040020",
    "广州": "050020", "深圳": "050090", "杭州": "070020", "成都": "280020",
    "武汉": "170020", "南京": "060020", "苏州": "060080", "西安": "270020",
    "长沙": "180020", "郑州": "200020", "青岛": "120020", "合肥": "150020",
    "厦门": "110020", "宁波": "070020", "东莞": "050090", "佛山": "050020",
}


def _headers(cookie: str) -> dict:
    h = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Origin": BASE,
        "Referer": BASE + "/",
        "X-Client-Type": "web",
        "X-Fscp-Version": "1.1",
        "X-Fscp-Std-Info": '{"client_id":"40108"}',
        "X-Fscp-Trace-Id": str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        h["Cookie"] = cookie
    return h


def _check(payload: dict) -> dict:
    if str(payload.get("flag")) == "1":
        return payload.get("data") or {}
    msg = payload.get("msg") or payload.get("message") or ""
    code = str(payload.get("code", ""))
    if "登录" in msg or code in ("-1001", "1001"):
        raise FetchError("AUTH_REQUIRED", f"猎聘要求登录：{msg}",
                         hint="在浏览器登录后导出 Cookie，用 --cookie 或 LIEPIN_COOKIE 传入")
    raise FetchError("BLOCKED", f"猎聘拒绝请求（code={code}）：{msg}",
                     hint="补全登录 Cookie 与请求头；数据中心 IP 常被 WAF 拦截，建议本机运行")


def _job_from_card(card: dict) -> dict | None:
    job = card.get("job") or card
    comp = card.get("comp") or {}
    if not (job.get("title") or job.get("jobTitle")):
        return None
    jid = str(job.get("jobId") or job.get("jobIdStr") or job.get("id") or "")
    link = job.get("link") or job.get("url") or (f"{BASE}/job/{jid}.shtml" if jid else "")
    tags = job.get("jobLabels") or job.get("labels") or job.get("welfare") or []
    if isinstance(tags, str):
        tags = [t for t in re.split(r"[,，|]", tags) if t]
    return norm_job(
        source="liepin",
        job_id=jid,
        title=job.get("title") or job.get("jobTitle", ""),
        company=(job.get("compName") or comp.get("compName")
                 or comp.get("companyName") or ""),
        salary=job.get("salary") or job.get("salaryDesc", ""),
        city=job.get("dqName") or job.get("cityName") or job.get("city", ""),
        district=job.get("districtName") or "",
        experience=job.get("requireWorkYears") or job.get("workYear", ""),
        degree=job.get("requireEduLevel") or job.get("eduLevel", ""),
        tags=[t if isinstance(t, str) else str(t) for t in tags],
        url=link,
        boss=job.get("recruiterName") or card.get("recruiterName", ""),
        industry=(job.get("compIndustry") or comp.get("compIndustry")
                  or comp.get("industry") or ""),
        size=job.get("compScale") or comp.get("compScale", ""),
        posted_at=str(job.get("refreshTime") or job.get("datePosted") or "")[:10],
    )


def search(query: str, city_code: str = "", page: int = 1, page_size: int = 40,
           cookie: str = "", timeout: float = 20, city_name: str = "",
           extra_params: dict | None = None, raw_file: str | None = None,
           debug: bool = False, **_kw) -> list[dict]:
    dq = CITY_CODES.get(city_name, "")
    form = {
        "city": dq,
        "dq": dq,
        "pubTime": "",
        "currentPage": max(0, page - 1),   # 猎聘从 0 开始
        "pageSize": page_size,
        "key": query,
        "suggestTag": "",
        "workYearCode": "0",
        "compId": "",
        "compName": "",
        "compTag": "",
        "industry": "",
        "salary": "",
        "jobKind": "",
        "compScale": "",
        "compKind": "",
        "compStage": "",
        "eduLevel": "",
    }
    if extra_params:
        form.update({k: str(v) for k, v in extra_params.items()})

    payload = {
        "data": {
            "mainSearchPcConditionForm": form,
            "passThroughForm": {"scene": "input", "skId": "", "fkId": "", "ckId": ""},
        },
        "headers": {},
    }

    if raw_file:
        with open(raw_file, encoding="utf-8") as f:
            resp = json.load(f)
    else:
        resp = post_json(SEARCH_API, payload, headers=_headers(cookie),
                         timeout=timeout, debug=debug)

    data = _check(resp)
    inner = data.get("data") if isinstance(data.get("data"), dict) else data
    cards = inner.get("jobCardList") or inner.get("jobList") or []
    jobs = [_job_from_card(c) for c in cards]
    jobs = [j for j in jobs if j]

    # 城市编码没收录时接口可能返回全国，这里按城市名兜底过滤
    if city_name and city_name not in ("全国",) and CITY_CODES.get(city_name) is None:
        jobs = [j for j in jobs if city_name in (j["city"] or "")]
    return jobs


def _job_id(value: str) -> str:
    v = value.strip()
    m = re.search(r"/job/(\d+)\.shtml", v) or re.search(r"[?&]jobId=(\d+)", v)
    if m:
        return m.group(1)
    if v.isdigit():
        return v
    raise FetchError("PARAM", f"无法从输入中解析猎聘职位 ID：{value}",
                     hint="传 search 结果里的 id，或形如 https://www.liepin.com/job/123.shtml 的链接")


def _find_jobposting(node):
    if isinstance(node, dict):
        t = node.get("@type")
        if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
            return node
        for v in node.values():
            found = _find_jobposting(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = _find_jobposting(v)
            if found:
                return found
    return None


def _detail_from_html(html: str, jid: str) -> dict:
    for raw in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, re.S):
        try:
            doc = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        posting = _find_jobposting(doc)
        if not posting:
            continue
        org = posting.get("hiringOrganization") or {}
        loc = posting.get("jobLocation") or {}
        addr = (loc.get("address") if isinstance(loc, dict) else {}) or {}
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
            addr = (loc.get("address") if isinstance(loc, dict) else {}) or {}
        desc = strip_html(posting.get("description") or "")
        return norm_job(
            source="liepin",
            job_id=jid,
            title=posting.get("title", ""),
            company=org.get("name", "") if isinstance(org, dict) else str(org),
            salary=_salary(posting.get("baseSalary")),
            city=addr.get("addressLocality", "") if isinstance(addr, dict) else "",
            district=addr.get("streetAddress", "") if isinstance(addr, dict) else "",
            experience=posting.get("experienceRequirements", "") if isinstance(
                posting.get("experienceRequirements"), str) else "",
            degree=posting.get("educationRequirements", "") if isinstance(
                posting.get("educationRequirements"), str) else "",
            tags=[t for t in (posting.get("employmentType") or []) if isinstance(t, str)]
            if isinstance(posting.get("employmentType"), list) else [],
            url=f"{BASE}/job/{jid}.shtml",
            description=desc,
            posted_at=str(posting.get("datePosted") or "")[:10],
        )

    # 兜底：常见正文容器
    m = re.search(r'<div[^>]*class="[^"]*(?:job-intro|job-description|content)[^"]*"[^>]*>(.*?)</div>',
                  html, re.S)
    if m:
        text = strip_html(m.group(1))
        if text:
            return norm_job(source="liepin", job_id=jid, title="", company="",
                            url=f"{BASE}/job/{jid}.shtml", description=text)
    raise FetchError("PARSE", "详情页里没找到 JobPosting JSON-LD",
                     hint="可能被风控或页面结构变了；用 --raw 保存 HTML 后补解析")


def _salary(v) -> str:
    if isinstance(v, dict):
        val = v.get("value") or {}
        if isinstance(val, dict):
            lo, hi = val.get("minValue"), val.get("maxValue")
            unit = val.get("unitText", "")
            if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and min(lo, hi) >= 1000:
                return f"{lo / 1000:g}-{hi / 1000:g}K" + (f"·{unit}" if unit and unit != "月" else "")
            if lo or hi:
                return f"{lo or ''}-{hi or ''}"
        return str(v.get("name") or "")
    return str(v or "")


def detail(job_id_or_url: str, cookie: str = "", timeout: float = 20,
           raw_file: str | None = None, debug: bool = False, **_kw) -> dict:
    jid = _job_id(job_id_or_url)
    if raw_file:
        text = open(raw_file, encoding="utf-8", errors="replace").read()
        if text.lstrip().startswith("<"):
            return _detail_from_html(text, jid)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as e:
            raise FetchError("PARSE", "raw 文件既不是 HTML 也不是 JSON") from e
        # 兼容直接保存的详情接口 JSON
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        data = data.get("data") if isinstance(data.get("data"), dict) else data
        job = data.get("job") or data.get("jobInfo") or data
        return _job_from_card({"job": job}) or norm_job(source="liepin", job_id=jid,
                                                        title="", company="")

    url = f"{BASE}/job/{jid}.shtml"
    status, html = request(url, headers={"Referer": BASE + "/", **_headers(cookie)},
                           timeout=timeout, debug=debug)
    if status != 200 or "<html" not in html[:500].lower():
        raise FetchError("BLOCKED", f"详情页返回异常（HTTP {status}）",
                         hint="猎聘对未登录/机房 IP 会返回验证页；请在本机带 Cookie 运行")
    return _detail_from_html(html, jid)


def url_for(job: dict) -> str:
    return job.get("url") or ""
