"""离线演示适配器：用内置样例数据跑通 search → detail → /apply 全流程。"""
from __future__ import annotations

import json
from pathlib import Path

from net import FetchError

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "demo_jobs.json"


def _load() -> list[dict]:
    with FIXTURE.open(encoding="utf-8") as f:
        return json.load(f)["jobs"]


def search(query: str = "", city_code: str = "100010000", page: int = 1,
           page_size: int = 20, **_kw) -> list[dict]:
    q = (query or "").lower()
    jobs = []
    for job in _load():
        hay = " ".join([job.get("title", ""), job.get("company", ""),
                        " ".join(job.get("tags") or []), job.get("description", "")]).lower()
        if q and q not in hay:
            continue
        if city_code != "100010000" and job.get("city_code") != city_code:
            continue
        jobs.append({k: v for k, v in job.items() if k != "city_code"})
    start = max(0, (page - 1) * page_size)
    return jobs[start:start + page_size]


def detail(job_id_or_url: str, **_kw) -> dict:
    for job in _load():
        if job_id_or_url in (job.get("id"), job.get("url")):
            return {k: v for k, v in job.items() if k != "city_code"}
    raise FetchError("NOT_FOUND", f"演示数据里没有 {job_id_or_url}",
                     hint="先跑 search --provider demo 看可用 ID")
