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

## 后续可接的站点（线索）

- **猎聘**：`POST https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job`
  body 里是 `mainSearchPcConditionForm`（`key` / `city` / `dq` / `currentPage` /
  `pageSize` …），需要 `X-Client-Type: web`、`X-Fscp-Version: 1.1` 与登录 Cookie。
  返回 `data.data.jobCardList[].job`。
- **51job**：`https://we.51job.com/api/job/search-pc`，带 `sign` 参数 + WAF Cookie，
  难度较高，建议先做浏览器侧导出再解析。
- **拉勾**：App 接口带签名，需逆向，稳定性差。

新增 provider 的步骤见 `SKILL.md` 与 `cli/README.md`。
