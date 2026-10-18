---
name: cn-jobs-search
version: 0.1.0
description: >
  Use this skill whenever the user wants to search for jobs in mainland China, look up
  a Chinese job posting, or asks about the Chinese job market — even if they never name
  a job board. Trigger for phrases like 找工作、招聘、职位、岗位、求职、投简历、内推、
  BOSS直聘、boss、直聘、智联、猎聘、51job、前程无忧、拉勾、薪资、北京/上海/深圳/杭州…
  的岗位, "有没有 python 岗位", "帮我找大模型的工作", "这个 JD 怎么样", "查一下这个职位".
  Also trigger when the user pastes a zhipin.com / liepin.com / 51job.com job URL.
  Do NOT use for overseas job markets — those have their own portal skills.
context: fork
enabled: true
allowed-tools: Bash(python3 .agents/skills/cn-jobs-search/cli/src/cli.py *)
---

# 国内职位检索（cn-jobs-search）

用一条 CLI 在国内招聘平台检索职位、拉取完整 JD，输出结构化结果，可直接交给
`/apply` 做匹配度评估和材料定制。

**当前数据源**

| provider | 状态 | 说明 |
|---|---|---|
| `boss` | live | BOSS 直聘 Web 接口。**需要登录 Cookie**，数据中心/海外 IP 会被风控（code=37） |
| `demo` | offline | 内置 6 条样例，无需网络，用于验证 search → detail → apply 全流程 |

> 真实站点都有反爬。本 CLI **不做验证码破解、不模拟登录**；它复用你自己浏览器里
> 的会话 Cookie。请控制频率（默认单次请求，人工节奏），遵守目标站点条款。

## 何时使用

- 用户想按关键词/城市找岗位（"北京有哪些 Python 后端岗位"）
- 用户给了一个职位链接，想读完整 JD、判断是否值得投
- 需要把岗位列表交给 `/rank` 批量打分，或交给 `/apply` 生成定制简历
- 用户问某个岗位的薪资、经验、学历要求

## 命令

所有命令都在**仓库根目录**执行：

```bash
python3 .agents/skills/cn-jobs-search/cli/src/cli.py <command> [flags]
```

### search — 搜索职位

```bash
python3 .agents/skills/cn-jobs-search/cli/src/cli.py search \
  --query "python 后端" --city 北京 --limit 10 --format table
```

| flag | 说明 |
|---|---|
| `--query` / `-q` | 关键词（岗位名、技能、公司）。`boss` 必填；`demo` 可空 |
| `--city` / `-c` | 中文名 / 拼音 / 9 位城市码 / `全国`（默认全国） |
| `--page` | 页码，从 1 开始 |
| `--limit` / `-n` | 最多输出条数（客户端截断，默认 20） |
| `--page-size` | 单页抓取条数（默认 30） |
| `--provider` / `-p` | `boss`（默认）或 `demo` |
| `--format` / `-f` | `table`（默认）、`json`、`plain` |
| `--raw FILE` | 不联网，解析已保存的接口 JSON（调试/离线） |
| `--param K=V` | 透传 BOSS 查询参数，可重复（如 `--param experience=103`） |
| `--cookie` / `--cookie-file` | 登录 Cookie（见下） |
| `--timeout` | 单次请求超时秒数（默认 20） |
| `--debug` | 把 HTTP 状态打到 stderr |

### detail — 拉取完整 JD

```bash
python3 .agents/skills/cn-jobs-search/cli/src/cli.py detail <ID或链接> --format plain
```

`ID` 来自 search 结果（JSON 里的 `id`，即 `securityId`/`encryptJobId`），也可以直接传
`https://www.zhipin.com/job_detail/xxx.html?securityId=...`。

### providers — 看数据源状态

```bash
python3 .agents/skills/cn-jobs-search/cli/src/cli.py providers
```

## 推荐工作流

1. **先 demo 验证链路**（无网络也能跑）：
   ```bash
   python3 .agents/skills/cn-jobs-search/cli/src/cli.py search -q "llm" -p demo -f json
   ```
2. **真实检索**：确认 Cookie 可用后
   ```bash
   python3 .agents/skills/cn-jobs-search/cli/src/cli.py search -q "大模型 应用" --city 北京 -n 15 -f json
   ```
3. **挑 2–3 个岗位拉详情**：`detail <id> -f plain`，把 JD 交给 `/apply`：
   ```
   /apply <粘贴 detail 输出的全文>
   ```
4. **批量筛选**：search 的 JSON 直接喂给 `/rank`（字段：title/company/salary/city/
   experience/degree/tags/url），让打分 agent 只对入围岗位调 detail。

**给 agent 的约定**：`-f json` 输出 `{ok, provider, query, city, page, count, jobs[]}`；
失败输出 `{ok:false, error:{code, message, hint}}` 并用非零退出码区分原因。
优先读 `error.code` 决定下一步（见下表），不要盲目重试。

## Cookie 怎么配

BOSS 的搜索接口要求登录态，关键的 Cookie 是 `__zp_stoken__`（还有 `lastCity` 等）。

1. 浏览器登录 `zhipin.com`；
2. DevTools → Network → 任意 `wapi` 请求 → 复制请求头里的 `Cookie:` 整行；
3. 三选一传入：
   ```bash
   # A. 直接传
   --cookie "lastCity=101010100; __zp_stoken__=...; ..."

   # B. 环境变量（推荐，避免进 shell history）
   export BOSS_COOKIE="lastCity=...; __zp_stoken__=..."
   python3 .../cli.py search -q python

   # C. 浏览器导出 cookies.txt（Netscape 格式）
   python3 .../cli.py search -q python --cookie-file ~/cookies.txt
   ```

Cookie 会过期（通常几天到几周），失效时重新导出即可。

## 错误码与对策

| code | 退出码 | 含义 | 怎么办 |
|---|---|---|---|
| `MISSING_REQUIRED` | 2 | 缺 `--query` | 补关键词 |
| `PARAM` | 2 | 城市/参数不合法 | 看提示里的可用城市 |
| `BLOCKED` | 3 | 风控（BOSS code=37/17） | 换本机网络、更新 Cookie、降频、隔几分钟再试 |
| `AUTH_REQUIRED` | 4 | 未登录/验证过期 | 重新导出 Cookie |
| `API_ERROR` | 5 | 接口返回未知 code | 保存 `--debug` 输出，可能是接口变更 |
| `NETWORK` | 6 | 超时/DNS/TLS | 检查网络/代理 |
| `PARSE` | 7 | 返回 HTML 而非 JSON | 几乎都是风控页，按 BLOCKED 处理 |
| `NOT_FOUND` | 8 | demo 数据里没有该 ID | 先 search 拿 ID |

## 输出字段

```json
{
  "id": "enc-...", "source": "boss",
  "title": "Python 后端工程师", "company": "云启科技",
  "salary": "25-40K·14薪", "city": "北京", "district": "朝阳区·望京",
  "experience": "3-5年", "degree": "本科",
  "tags": ["Python", "FastAPI"], "url": "https://www.zhipin.com/job_detail/...",
  "description": "……", "boss": "李女士 HR",
  "industry": "企业服务", "size": "100-499人", "posted_at": "2026-10-17"
}
```

`description` 只在 `detail` 里有值（已把 HTML 转成纯文本）。

## 边界与合规

- **不**绕过验证码、**不**模拟登录、**不**使用他人 Cookie。
- 单次查询、人工节奏；不要写循环高频抓取。
- 岗位信息版权归原平台，仅用于个人求职。
- 接口随时可能变；变了就用 `--raw` 保存真实响应，更新
  `cli/tests/fixtures/` 与解析逻辑（见 `cli/README.md`）。
- 平台条款若禁止自动化访问，请以平台规则为准，改用官方 API/手动复制 JD。

## 扩展新站点（猎聘 / 51job / 拉勾…）

1. 在 `cli/src/providers/` 新建 `xxx.py`，实现：
   ```python
   def search(query, city_code, page=1, page_size=30, cookie="", timeout=20,
              raw_file=None, debug=False) -> list[dict]
   def detail(job_id_or_url, cookie="", timeout=20, raw_file=None, debug=False) -> dict
   ```
   用 `base.norm_job(...)` 返回统一结构。
2. 在 `providers/__init__.py` 的 `REGISTRY` 与 `_META` 注册。
3. 把真实响应存到 `cli/tests/fixtures/`，补一个 `tests/test_xxx.py`。
4. 更新本文件的 provider 表格与 `url-reference.md`。
