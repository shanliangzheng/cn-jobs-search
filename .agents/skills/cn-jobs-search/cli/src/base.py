"""共享逻辑：城市码、HTML 转文本、结果归一化、终端表格。"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from html.parser import HTMLParser

# --------------------------------------------------------------------- 城市
# BOSS 直聘的城市编码（常用城市，可在 url-reference.md 里补全）
CITY_CODES = {
    "北京": "101010100", "上海": "101020100", "天津": "101030100",
    "重庆": "101040100", "哈尔滨": "101050100", "长春": "101060100",
    "沈阳": "101070100", "大连": "101070200", "石家庄": "101090100",
    "太原": "101100100", "西安": "101110100", "济南": "101120100",
    "青岛": "101120200", "郑州": "101180100", "南京": "101190100",
    "无锡": "101190200", "苏州": "101190400", "南通": "101190500",
    "常州": "101191100", "杭州": "101210100", "宁波": "101210400",
    "温州": "101210700", "合肥": "101220100", "福州": "101230100",
    "厦门": "101230200", "南昌": "101240100", "长沙": "101250100",
    "武汉": "101200100", "广州": "101280100", "深圳": "101280600",
    "东莞": "101281600", "佛山": "101280800", "珠海": "101281700",
    "中山": "101281800", "惠州": "101280900", "成都": "101270100",
    "贵阳": "101260100", "昆明": "101290100", "南宁": "101300100",
    "海口": "101310100",
}

CITY_ALIASES = {
    "beijing": "北京", "shanghai": "上海", "guangzhou": "广州", "shenzhen": "深圳",
    "hangzhou": "杭州", "chengdu": "成都", "wuhan": "武汉", "xian": "西安",
    "nanjing": "南京", "suzhou": "苏州", "tianjin": "天津", "chongqing": "重庆",
    "changsha": "长沙", "zhengzhou": "郑州", "qingdao": "青岛", "hefei": "合肥",
    "xiamen": "厦门", "fuzhou": "福州", "jinan": "济南", "dalian": "大连",
    "shenyang": "沈阳", "harbin": "哈尔滨", "kunming": "昆明", "guiyang": "贵阳",
    "nanning": "南宁", "haikou": "海口", "wuxi": "无锡", "changchun": "长春",
    "shijiazhuang": "石家庄", "taiyuan": "太原", "nanchang": "南昌", "wenzhou": "温州",
    "ningbo": "宁波", "dongguan": "东莞", "foshan": "佛山", "zhuhai": "珠海",
    "zhongshan": "中山", "huizhou": "惠州", "changzhou": "常州", "nantong": "南通",
    "全国": "全国", "all": "全国",
}


def resolve_city(value: str | None) -> tuple[str, str]:
    """城市名/拼音/编码 → (code, 展示名)。空值默认全国。"""
    if not value:
        return "100010000", "全国"
    v = value.strip()
    if re.fullmatch(r"\d{9}", v):
        name = next((k for k, c in CITY_CODES.items() if c == v), v)
        return v, name
    v = v.lower()
    name = CITY_ALIASES.get(v, value.strip())
    if name in CITY_CODES:
        return CITY_CODES[name], name
    if name == "全国":
        return "100010000", "全国"
    raise ValueError(f"不认识的城市：{value}；可用：{'、'.join(sorted(CITY_CODES))}、全国")


# --------------------------------------------------------------------- HTML
_BLOCK = {"p", "div", "br", "li", "ul", "ol", "tr", "h1", "h2", "h3", "h4", "section", "article"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "li":
            self.parts.append("\n• ")
        elif tag in _BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        elif tag in _BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def strip_html(raw: str | None) -> str:
    if not raw:
        return ""
    p = _TextExtractor()
    p.feed(raw)
    text = "".join(p.parts)
    text = html.unescape(text)
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------- 归一化
def norm_job(*, source: str, job_id: str, title: str, company: str, salary: str = "",
             city: str = "", district: str = "", experience: str = "", degree: str = "",
             tags=None, url: str = "", description: str = "", boss: str = "",
             industry: str = "", size: str = "", posted_at: str = "") -> dict:
    tags = [t for t in (tags or []) if t]
    return {
        "id": str(job_id or ""),
        "source": source,
        "title": (title or "").strip(),
        "company": (company or "").strip(),
        "salary": (salary or "").strip(),
        "city": (city or "").strip(),
        "district": (district or "").strip(),
        "experience": (experience or "").strip(),
        "degree": (degree or "").strip(),
        "tags": tags,
        "url": url,
        "description": description or "",
        "boss": boss,
        "industry": industry,
        "size": size,
        "posted_at": posted_at,
    }


# --------------------------------------------------------------------- 输出
def cw(ch: str) -> int:
    if unicodedata.combining(ch):
        return 0
    if 0x1F300 <= ord(ch) <= 0x1FAFF or 0x2600 <= ord(ch) <= 0x27BF:
        return 2
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def dw(s: str) -> int:
    return sum(cw(c) for c in s)


def clip(s: str, width: int) -> str:
    if dw(s) <= width:
        return s
    out, acc = "", 0
    for ch in s:
        c = cw(ch)
        if acc + c > width - 1:
            break
        out += ch
        acc += c
    return out + "…"


def fmt_table(jobs: list[dict]) -> str:
    if not jobs:
        return "没有结果。"
    headers = ["标题", "公司", "薪资", "城市", "经验", "学历", "标签"]
    keys = ["title", "company", "salary", "city", "experience", "degree", "tags"]
    caps = [28, 18, 12, 10, 8, 6, 24]

    rows = []
    for j in jobs:
        vals = []
        for k, cap in zip(keys, caps):
            v = " ".join(j.get(k, [])) if k == "tags" else str(j.get(k, "") or "")
            vals.append(clip(v, cap))
        rows.append(vals)

    widths = []
    for i, h in enumerate(headers):
        widths.append(min(max([dw(h)] + [dw(r[i]) for r in rows]), caps[i]))

    def line(cells, sep="│"):
        return sep + " " + f" {sep} ".join(c + " " * (w - dw(c)) for c, w in zip(cells, widths)) + " " + sep

    out = [line(headers), "├" + "┼".join("─" * (w + 2) for w in widths) + "┤"]
    out += [line(r) for r in rows]
    return "\n".join(out)


def fmt_plain(job: dict, index: int | None = None) -> str:
    head = f"{index}. {job['title']}" if index else job["title"]
    lines = [head]
    meta = [x for x in [job.get("company"), job.get("salary"), job.get("city"),
                        job.get("district"), job.get("experience"), job.get("degree")] if x]
    if meta:
        lines.append(" · ".join(meta))
    if job.get("tags"):
        lines.append("标签：" + " / ".join(job["tags"]))
    if job.get("url"):
        lines.append("链接：" + job["url"])
    if job.get("id"):
        lines.append("ID：" + str(job["id"]))
    if job.get("description"):
        lines.append("")
        for ln in job["description"].splitlines():
            lines.append(("  " + ln).rstrip() if ln.strip() else "")
    return "\n".join(lines)


def dump(jobs, fmt: str, detail: bool = False) -> str:
    if fmt == "json":
        return json.dumps(jobs, ensure_ascii=False, indent=2)
    if detail:
        return fmt_plain(jobs[0])
    if fmt == "plain":
        return "\n\n".join(fmt_plain(j, i + 1) for i, j in enumerate(jobs))
    return fmt_table(jobs)
