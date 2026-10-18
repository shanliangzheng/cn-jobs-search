# cn-jobs-search CLI

纯 Python 3.10+ 标准库，无第三方依赖，也不需要 Bun。

## 目录

```
cli/
├── src/
│   ├── cli.py            # 入口：search / detail / providers
│   ├── base.py           # 城市码、HTML→文本、归一化、表格输出
│   ├── net.py            # urllib 封装：超时、重试、错误码
│   ├── cookies.py        # Cookie 字符串 / cookies.txt
│   └── providers/
│       ├── __init__.py   # REGISTRY + 元信息
│       ├── boss.py       # BOSS 直聘
│       ├── liepin.py     # 猎聘（experimental）
│       └── demo.py       # 离线样例
├── fixtures/
│   └── demo_jobs.json    # demo 数据
└── tests/                # unittest，无网络
```

## 跑测试

```bash
cd .agents/skills/cn-jobs-search/cli
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

测试覆盖：城市解析、HTML 清洗、归一化、BOSS 列表/详情解析、code=37 映射、
猎聘搜索/JSON-LD 详情、Cookie 解析、demo 过滤/分页、CLI 退出码与 JSON 契约（36 个用例）。

## 新增一个站点

1. 复制 `providers/boss.py` 改造成 `providers/xxx.py`：

   ```python
   def search(query, city_code, page=1, page_size=30, cookie="", timeout=20,
              raw_file=None, debug=False) -> list[dict]:
       ...
       return [norm_job(source="xxx", job_id=..., title=..., ...)]

   def detail(job_id_or_url, cookie="", timeout=20, raw_file=None, debug=False) -> dict:
       ...
   ```

   - 所有网络请求走 `net.request/get_json/post_json`，这样超时/重试/错误码统一。
   - 解析失败用 `FetchError("PARSE", ..., hint=...)`，风控用 `FetchError("BLOCKED", ...)`。
   - `raw_file` 分支必须支持：把真实响应存成 JSON 后，不联网也能解析。

2. 在 `providers/__init__.py` 注册：

   ```python
   from . import boss, demo, xxx
   REGISTRY = {"boss": boss, "demo": demo, "xxx": xxx}
   ```

3. 存一份真实响应到 `tests/fixtures/xxx_search.json`，写 `tests/test_xxx.py`。
4. 更新 `SKILL.md` 的 provider 表与 `url-reference.md`。

## 调试风控/接口变更

```bash
# 保存真实响应
curl -sS 'https://www.zhipin.com/wapi/zpgeek/search/joblist.json?...' \
  -H 'Cookie: __zp_stoken__=...' -o /tmp/boss.json

# 离线解析，验证字段名有没有变
python3 src/cli.py search -q python --raw /tmp/boss.json -f json
```

这样就能在完全不碰网络的情况下迭代解析逻辑。

## 设计约定

- **不模拟登录、不破解验证码**，只用调用方自己的 Cookie。
- 单次调用单次请求；不做并发爬取。
- 退出码稳定，便于 agent 判断：2 参数、3 风控、4 登录、5 接口、6 网络、7 解析、8 未找到。
- `--format json` 永远输出一个 JSON 对象（成功或失败），不混入日志；日志走 stderr。
