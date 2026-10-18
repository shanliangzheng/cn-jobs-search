# 接口与城市码参考

> 这些都是站点 Web 前端在用的非公开接口，随时可能变。改动后用
> `--raw` 保存真实响应，更新 `cli/tests/fixtures/`。

## BOSS 直聘

### 搜索

```
GET https://www.zhipin.com/wapi/zpgeek/search/joblist.json
```

| 参数 | 说明 |
|---|---|
| `scene=1` | 固定 |
| `query` | 关键词 |
| `city` | 9 位城市码，全国 `100010000` |
| `page` | 从 1 开始 |
| `pageSize` | 默认 30，上限约 30 |
| `experience` | 经验编码，如 `103`（1-3 年）、`104`（3-5 年）、`105`（5-10 年） |
| `degree` | 学历编码，如 `203`（本科）、`204`（硕士） |
| `salary` | 薪资编码，如 `405`（20-30K） |
| `industry` | 行业编码 |
| `scale` | 公司规模编码 |
| `stage` | 融资阶段编码 |

编码以站点筛选器的实际请求为准；不确定就用 `--param` 透传试。

### 详情

```
GET https://www.zhipin.com/wapi/zpgeek/job/detail.json?securityId=<securityId>
```

### 响应（成功）

```json
{
  "code": 0,
  "message": "Success",
  "zpData": {
    "jobList": [{
      "securityId": "...", "encryptJobId": "...",
      "jobName": "Python 后端工程师", "salaryDesc": "25-40K·14薪",
      "brandName": "云启科技", "brandIndustry": "企业服务",
      "brandScaleName": "100-499人", "brandStageName": "B轮",
      "cityName": "北京", "areaDistrict": "朝阳区", "businessDistrict": "望京",
      "jobExperience": "3-5年", "jobDegree": "本科",
      "jobLabels": ["Python"], "skills": ["FastAPI"],
      "welfareList": ["五险一金"], "bossName": "李女士", "bossTitle": "HR",
      "lastModifyTime": 1792332837000
    }],
    "hasMore": true
  }
}
```

详情把 `jobList` 换成 `jobInfo` / `brandInfo` / `bossInfo`，JD 正文在
`jobInfo.jobDescription`（HTML）。

### 常见 code

| code | 含义 | CLI 映射 |
|---|---|---|
| 0 | 成功 | — |
| 37 | 您的环境存在异常 | `BLOCKED` |
| 17 | 请求过于频繁 | `BLOCKED` |
| 1 / 7 / 101 | 未登录 / 需要安全验证 | `AUTH_REQUIRED` |

### 关键 Cookie

| Cookie | 作用 |
|---|---|
| `__zp_stoken__` | 风控令牌，必需 |
| `lastCity` | 上次城市，影响默认值 |
| `zp_at` / `wt2` 等 | 登录态，视账号而定 |

## 城市码（BOSS，常用）

| 城市 | code | 城市 | code |
|---|---|---|---|
| 全国 | 100010000 | 北京 | 101010100 |
| 上海 | 101020100 | 天津 | 101030100 |
| 重庆 | 101040100 | 哈尔滨 | 101050100 |
| 长春 | 101060100 | 沈阳 | 101070100 |
| 大连 | 101070200 | 石家庄 | 101090100 |
| 太原 | 101100100 | 西安 | 101110100 |
| 济南 | 101120100 | 青岛 | 101120200 |
| 郑州 | 101180100 | 南京 | 101190100 |
| 无锡 | 101190200 | 苏州 | 101190400 |
| 南通 | 101190500 | 常州 | 101191100 |
| 杭州 | 101210100 | 宁波 | 101210400 |
| 温州 | 101210700 | 合肥 | 101220100 |
| 福州 | 101230100 | 厦门 | 101230200 |
| 南昌 | 101240100 | 长沙 | 101250100 |
| 武汉 | 101200100 | 广州 | 101280100 |
| 深圳 | 101280600 | 东莞 | 101281600 |
| 佛山 | 101280800 | 珠海 | 101281700 |
| 中山 | 101281800 | 惠州 | 101280900 |
| 成都 | 101270100 | 贵阳 | 101260100 |
| 昆明 | 101290100 | 南宁 | 101300100 |
| 海口 | 101310100 | | |

不在表里的城市：浏览器里选一次城市，从请求 URL 的 `city=` 取值，再直接传 9 位码。

## 猎聘（experimental）

### 搜索

```
POST https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job
```

请求体：

```json
{
  "data": {
    "mainSearchPcConditionForm": {
      "city": "280020", "dq": "280020", "pubTime": "",
      "currentPage": 0, "pageSize": 40, "key": "实车测试",
      "suggestTag": "", "workYearCode": "0",
      "compId": "", "compName": "", "compTag": "", "industry": "",
      "salary": "", "jobKind": "", "compScale": "", "compKind": "",
      "compStage": "", "eduLevel": ""
    },
    "passThroughForm": {"scene": "input", "skId": "", "fkId": "", "ckId": ""}
  },
  "headers": {}
}
```

必要请求头：

```
Content-Type: application/json;charset=UTF-8
X-Client-Type: web
X-Fscp-Version: 1.1
X-Fscp-Std-Info: {"client_id":"40108"}
X-Fscp-Trace-Id: <uuid>
X-Requested-With: XMLHttpRequest
Origin: https://www.liepin.com
Referer: https://www.liepin.com/
Cookie: <登录态>
```

响应：`flag=1` 成功，`data.data.jobCardList[]`；每项里 `job` 是职位、
`comp` 是公司、`recruiter` 是招聘者。`flag=0` 看 `code/msg`
（`-1400` 多为参数/请求头不全或被 WAF 拦）。

### 详情

`GET https://www.liepin.com/job/<jobId>.shtml`，从页面里的
`<script type="application/ld+json">` 取 schema.org `JobPosting`：
`title`、`description`、`hiringOrganization.name`、`jobLocation.address`、
`datePosted`、`baseSalary.value`。

### 城市编码（猎聘自己的 dq）

| 城市 | dq | 城市 | dq |
|---|---|---|---|
| 北京 | 010 | 上海 | 020 |
| 天津 | 030020 | 重庆 | 040020 |
| 广州 | 050020 | 深圳 | 050090 |
| 杭州 | 070020 | 成都 | 280020 |
| 武汉 | 170020 | 南京 | 060020 |
| 苏州 | 060080 | 西安 | 270020 |
| 长沙 | 180020 | 郑州 | 200020 |
| 青岛 | 120020 | 合肥 | 150020 |
| 厦门 | 110020 | 宁波 | 070020 |

> 未收录的城市：CLI 传空 dq（接口给全国），再按 `dqName` 过滤。
> 这层映射按公开资料整理，如与站点不符，改 `providers/liepin.py` 的 `CITY_CODES`。

## 后续可接的站点（线索）

- **51job**：`https://we.51job.com/api/job/search-pc`，带 `sign` 参数 + WAF Cookie，
  难度较高，建议先做浏览器侧导出再解析。
- **拉勾**：App 接口带签名，需逆向，稳定性差。

新增 provider 的步骤见 `SKILL.md` 与 `cli/README.md`。
