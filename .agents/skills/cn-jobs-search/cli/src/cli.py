#!/usr/bin/env python3
"""cn-jobs-search — 国内招聘网站职位检索 CLI（BOSS 直聘 + 离线演示）。

设计目标：给 Claude Code / Codex 等 agent 提供稳定的 `search` → `detail` 契约，
输出可直接喂给 ai-job-search 的 /apply 流程。

示例：
    python3 cli/src/cli.py search -q "python 后端" --city 北京 --limit 10
    python3 cli/src/cli.py search -q "llm" --provider demo
    python3 cli/src/cli.py detail demo-llm-app --provider demo
    python3 cli/src/cli.py providers
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cookies as cookie_mod  # noqa: E402
from base import dump, resolve_city  # noqa: E402
from net import FetchError  # noqa: E402
from providers import REGISTRY, describe  # noqa: E402

EXIT = {
    "MISSING_REQUIRED": 2,
    "PARAM": 2,
    "BLOCKED": 3,
    "AUTH_REQUIRED": 4,
    "API_ERROR": 5,
    "NETWORK": 6,
    "PARSE": 7,
    "NOT_FOUND": 8,
}


def _add_common(p: argparse.ArgumentParser, detail: bool = False) -> None:
    p.add_argument("--provider", "-p", default="boss", choices=sorted(REGISTRY),
                   help="数据源（默认 boss；demo 为离线样例）")
    if not detail:
        p.add_argument("--query", "-q", help="关键词，如 \"python 后端\"、\"大模型\"")
        p.add_argument("--city", "-c", default="全国", help="城市名/拼音/9 位编码，默认全国")
        p.add_argument("--page", type=int, default=1, help="页码，从 1 开始")
        p.add_argument("--limit", "-n", type=int, default=20, help="最多输出多少条")
        p.add_argument("--page-size", type=int, default=30, help="每页抓取条数")
        p.add_argument("--raw", metavar="FILE",
                       help="不从网络抓，直接解析已保存的接口 JSON（调试用）")
    p.add_argument("--format", "-f", default="table", choices=["table", "json", "plain"],
                   help="输出格式（默认 table）")
    p.add_argument("--cookie", help="Cookie 字符串（也可用 BOSS_COOKIE / CN_JOBS_COOKIE）")
    p.add_argument("--cookie-file", help="Netscape cookies.txt 路径")
    p.add_argument("--timeout", type=float, default=20, help="单次请求超时秒数")
    p.add_argument("--debug", action="store_true", help="把 HTTP 状态打到 stderr")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cn-jobs-search", description="国内招聘职位检索")
    ap.add_argument("--version", action="version", version="cn-jobs-search 0.2.0")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="搜索职位")
    _add_common(s)
    s.add_argument("--param", action="append", metavar="K=V", default=[],
                   help="透传给数据源的额外查询参数（BOSS / 猎聘），可重复，如 --param experience=103")

    d = sub.add_parser("detail", help="获取职位详情")
    _add_common(d, detail=True)
    d.add_argument("id", help="职位 ID（search 结果里的 ID）或带 securityId 的链接")
    d.add_argument("--raw", metavar="FILE", help="解析已保存的详情 JSON（调试用）")

    sub.add_parser("providers", help="列出可用数据源")
    return ap


def _fail(err: FetchError, fmt: str) -> int:
    code = EXIT.get(err.code, 1)
    if fmt == "json":
        print(json.dumps({"ok": False, "error": err.as_dict()}, ensure_ascii=False, indent=2))
    else:
        print(f"错误[{err.code}] {err.message}", file=sys.stderr)
        if err.hint:
            print(f"提示：{err.hint}", file=sys.stderr)
    return code


def _parse_params(pairs: list[str]) -> dict:
    out = {}
    for p in pairs:
        if "=" not in p:
            raise FetchError("PARAM", f"--param 需要 K=V 形式：{p}")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "providers":
        print(json.dumps(describe(), ensure_ascii=False, indent=2))
        return 0

    provider = REGISTRY[args.provider]
    fmt = args.format

    try:
        if args.cmd == "search":
            query = (args.query or "").strip()
            if not query and args.provider != "demo":
                raise FetchError("MISSING_REQUIRED", "缺少 --query",
                                 hint='例如：search -q "python 后端" --city 北京')
            city_code, city_name = resolve_city(args.city)
            domain = "liepin.com" if args.provider == "liepin" else "zhipin.com"
            cookie = cookie_mod.resolve(args.cookie, args.cookie_file, args.provider,
                                        domain=domain)
            kw = {}
            if args.provider in ("boss", "liepin"):
                kw = dict(extra_params=_parse_params(args.param))
            jobs = provider.search(
                query=query, city_code=city_code, city_name=city_name,
                page=args.page, page_size=args.page_size, cookie=cookie,
                timeout=args.timeout, raw_file=args.raw, debug=args.debug, **kw,
            )
            jobs = jobs[:max(0, args.limit)]
            if fmt == "json":
                print(json.dumps({"ok": True, "provider": args.provider, "query": query,
                                  "city": city_name, "page": args.page,
                                  "count": len(jobs), "jobs": jobs},
                                 ensure_ascii=False, indent=2))
            elif fmt == "plain":
                print(dump(jobs, "plain") or "没有结果。")
            else:
                print(dump(jobs, fmt))
            return 0

        if args.cmd == "detail":
            domain = "liepin.com" if args.provider == "liepin" else "zhipin.com"
            cookie = cookie_mod.resolve(args.cookie, args.cookie_file, args.provider,
                                        domain=domain)
            job = provider.detail(args.id, cookie=cookie, timeout=args.timeout,
                                  raw_file=args.raw, debug=args.debug)
            if fmt == "json":
                print(json.dumps({"ok": True, "provider": args.provider, "job": job},
                                 ensure_ascii=False, indent=2))
            else:
                print(dump([job], fmt, detail=True))
            return 0

    except FetchError as e:
        return _fail(e, fmt)
    except ValueError as e:  # 城市解析
        return _fail(FetchError("PARAM", str(e)), fmt)

    return 1


if __name__ == "__main__":
    sys.exit(main())
