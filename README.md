# cn-jobs-search — 国内招聘 skill（for ai-job-search）

给 [`MadsLorentzen/ai-job-search`](https://github.com/MadsLorentzen/ai-job-search) 补一个
**中国大陆**的职位检索 skill。原仓库自带的是丹麦市场（Jobindex / Jobnet / LinkedIn 等），
这套是按它的结构写的替代/补充。

- 数据源：**BOSS 直聘**（live，需要你自己的登录 Cookie）+ **demo**（离线样例）
- 依赖：**只要 Python 3.10+**，不需要 Bun、不需要 npm 包
- 输出：统一 JSON / 表格 / 纯文本，直接喂给 `/rank`、`/apply`
- 不含验证码破解、不模拟登录、不做高频抓取

## 目录

```
.ai-job-search-cn/
├── install.sh                                  # 复制到你的 fork
└── .agents/skills/cn-jobs-search/
    ├── SKILL.md                                # 给 agent 的说明书（含触发词）
    ├── url-reference.md                        # 接口、城市码、错误码
    └── cli/
        ├── README.md
        ├── src/{cli,base,net,cookies}.py
        ├── src/providers/{__init__,boss,demo}.py
        ├── fixtures/demo_jobs.json
        └── tests/                              # 29 个用例，不联网
```

## 安装

```bash
# 1) 放到你的 ai-job-search 仓库里
./install.sh /path/to/ai-job-search

# 2) 验证（离线，不碰网络）
cd /path/to/ai-job-search
python3 .agents/skills/cn-jobs-search/cli/src/cli.py search -q "llm" -p demo
python3 .agents/skills/cn-jobs-search/cli/src/cli.py detail demo-llm-app -p demo

# 3) 跑测试
cd .agents/skills/cn-jobs-search/cli
python3 -m unittest discover -s tests -p 'test_*.py'
```

也可以手动拷贝：把 `.agents/skills/cn-jobs-search/` 整个目录放进你仓库的同名路径即可。

> 仓库自带的 `tools/install_portal_clis.py` 只处理带 `package.json` 的 CLI，
> 这个 skill 会被自动跳过——它本来就不需要 `bun install`，不用管。

## 配 Cookie（用真实数据的前提）

BOSS 的搜索接口要登录态，关键是 `__zp_stoken__`：

1. 浏览器登录 <https://www.zhipin.com>；
2. DevTools → Network → 任一 `wapi` 请求 → 复制请求头的 `Cookie:`；
3. 用环境变量传（推荐）：

```bash
export BOSS_COOKIE="lastCity=101010100; __zp_stoken__=...; ..."
python3 .agents/skills/cn-jobs-search/cli/src/cli.py search -q "python 后端" --city 北京
```

或者 `--cookie "..."` / `--cookie-file ~/cookies.txt`（Netscape 格式）。

详细说明、错误码、城市码表见 `SKILL.md` 与 `url-reference.md`。

## 已知限制（重要）

- **数据中心/海外 IP 基本必被风控**：BOSS 会返回 `code=37 您的环境存在异常`。CLI 会给出
  明确提示并退出 3，不会假装成功。请在本机家庭网络 + 已登录浏览器下使用。
- Cookie 会过期，失效时重新导出。
- 接口是非公开 Web 接口，**随时可能变更**。变了用 `--raw` 保存真实响应，按
  `cli/README.md` 更新解析与 fixture。
- 只实现了 BOSS。猎聘/51job/拉勾的接入线索写在 `url-reference.md`，按同一接口扩展即可。
- 平台若禁止自动化访问，以平台条款为准；本工具定位是「复用你自己的登录态、低频查询」。

## 接到 `/scrape`、`/rank`、`/apply`

1. **搜索**：agent 看到「找工作 / 北京 python 岗位 / BOSS」这类请求会命中本 skill，
   执行 `search -f json`。
2. **排序**：把 JSON 里的 `jobs[]` 交给 `/rank` 批量打分（字段与它的输入兼容：
   title/company/salary/city/experience/degree/tags/url）。
3. **投递**：对入围岗位跑 `detail <id> -f plain`，把输出全文粘给
   `/apply <JD>`，或直接 `detail` 后把 URL 交给 `/apply`（若站点允许抓取）。
4. **偏好**：在 `search-queries.md` 里加上你的目标岗位/城市，`/setup --section search`
   时保持一致的表述。

## 为什么用 Python 而不是 Bun + TypeScript

- 原仓库的前置条件里本来就有 Python 3.10+，没有 Bun 的用户也能直接用；
- 零依赖、单文件入口，`python3 .../cli.py` 在 Claude Code / Codex 的 Bash 工具里最稳；
- 解析和测试都能离线跑，不受 Bun 版本影响。

想改回 TS 也可以：`providers/` 的契约就 `search()` / `detail()` 两个函数，
`SKILL.md` 里的 `allowed-tools` 换掉即可。

## 测试

```bash
cd .agents/skills/cn-jobs-search/cli
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

当前 **30 个用例全过**，覆盖：城市解析、HTML 清洗、表格宽度（中文/emoji）、
BOSS 列表与详情解析、`code=37` → `BLOCKED` 映射、Cookie 解析、
demo 过滤/分页、CLI 退出码与 JSON 契约。

## 许可

本 skill 为独立实现，与 BOSS 直聘、Anthropic 均无关联。代码可随你的
ai-job-search fork 一起使用；抓取到的岗位内容版权归原平台。
