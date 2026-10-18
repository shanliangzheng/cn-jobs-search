"""HTTP 小工具：超时、重试、退避、gzip/br 之外的纯文本抓取。"""
from __future__ import annotations

import json
import random
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

RETRY_STATUS = {403, 408, 425, 429, 500, 502, 503, 504}


class FetchError(Exception):
    """带错误码的抓取失败，CLI 会把它翻译成人类可读的提示。"""

    def __init__(self, code: str, message: str, hint: str = "", status: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status = status

    def as_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.hint:
            d["hint"] = self.hint
        if self.status:
            d["status"] = self.status
        return d


def _decode(body: bytes, content_type: str) -> str:
    charset = "utf-8"
    if "charset=" in content_type:
        charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
    return body.decode(charset, "replace")


def request(url: str,
            method: str = "GET",
            headers: dict | None = None,
            body: str | bytes | None = None,
            timeout: float = 20.0,
            retries: int = 3,
            backoff: float = 1.6,
            debug: bool = False) -> tuple[int, str]:
    """返回 (status, text)。失败抛 FetchError（NETWORK / BLOCKED / HTTP_ERROR）。"""
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive",
    }
    if headers:
        hdrs.update(headers)

    data = body.encode("utf-8") if isinstance(body, str) else body
    last = None

    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read()
                text = _decode(raw, resp.headers.get("Content-Type", ""))
                if debug:
                    print(f"[http] {method} {url} -> {resp.status} {len(raw)}B", file=__import__("sys").stderr)
                return resp.status, text
        except urllib.error.HTTPError as e:
            raw = e.read() or b""
            text = _decode(raw, e.headers.get("Content-Type", "") if e.headers else "")
            if debug:
                print(f"[http] {method} {url} -> HTTP {e.code} {len(raw)}B", file=__import__("sys").stderr)
            if e.code in RETRY_STATUS and attempt < retries - 1:
                last = FetchError("HTTP_ERROR", f"HTTP {e.code}", status=e.code)
                time.sleep(backoff ** attempt + random.random())
                continue
            if e.code in (401, 403, 429):
                raise FetchError("BLOCKED", f"HTTP {e.code}，被目标站点拦截",
                                 hint="换本机网络 / 配置登录 Cookie / 降低频率后再试", status=e.code)
            raise FetchError("HTTP_ERROR", f"HTTP {e.code}: {text[:200]}", status=e.code)
        except (socket.timeout, TimeoutError) as e:
            last = FetchError("NETWORK", f"请求超时：{e}")
        except urllib.error.URLError as e:
            last = FetchError("NETWORK", f"网络错误：{e.reason}")
        except ssl.SSLError as e:
            last = FetchError("NETWORK", f"TLS 错误：{e}")
        if attempt < retries - 1:
            time.sleep(backoff ** attempt + random.random())
    raise last or FetchError("NETWORK", "请求失败")


def get_json(url: str, **kw):
    status, text = request(url, **kw)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise FetchError("PARSE", f"返回的不是 JSON（{status}，{len(text)} 字节）",
                         hint="大概率是风控页/登录页，检查 Cookie 或换网络") from e


def post_json(url: str, payload: dict, **kw):
    headers = kw.pop("headers", {}) or {}
    headers.setdefault("Content-Type", "application/json")
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    status, text = request(url, method="POST", headers=headers, body=body, **kw)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise FetchError("PARSE", f"返回的不是 JSON（{status}，{len(text)} 字节）",
                         hint="接口可能要求登录 Cookie 或已变更") from e


__all__ = ["UA", "FetchError", "request", "get_json", "post_json", "urllib"]
