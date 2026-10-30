# B05-A：三条公开详情预览，待人工确认

批次：AUTO-20261030-2012。请求开始2026-10-30T20:12:28+08:00，结束20:12:38+08:00。6次请求全部HTTP200：robots、sitemap.xml、jobs-00.xml和3个详情。没有/api/、列表、登录、重试或并发；UA联系邮箱仅用于请求，落盘台账已脱敏。

## 实际预览

| 编号 | 名称 | 单位 | 地点 | 公告日期 | 截止/学历/专业/开放状态 | TXT |
|---|---|---|---|---|---|---|
| AUTO-01 | 市场经理 | 浙江沄生合成生物科技有限公司 | 台州市、椒江区 | 2026-07-09 | 均unknown | raw/AUTO-20261030-2012-01.evidence.txt |
| AUTO-02 | 英语品质工程师（应届生） | unknown | 东莞市 | 2026-08-19 | 均unknown | raw/AUTO-20261030-2012-02.evidence.txt |
| AUTO-03 | HRBP | unknown | 广州市 | 2026-06-26 | 均unknown | raw/AUTO-20261030-2012-03.evidence.txt |

完整字段、获取时间、来源URL和missing_fields在同名records.csv，原文和引用逐字存在于对应TXT。
首条介绍原文明确工作经验3年及以上，按原文留存，不表示适合大学毕业生。单位性质未核验，不把这批称作央国企岗位。

## 解析修正与证据版本

首次实际dry-run抓取了3条并发现隐私提示混入介绍，标题第二段有地区，附加标签污染招聘类型和日期。仅对已有可见文本进行了两次离线重解析，不重新抓取这3个URL，也未继续抓30条。run.json的offline_revisions记录旧/新证据哈希、修正原因与时点；获取时刻、HTTP状态和请求计数未改写。未保存整页HTML，没有复制或改动任何native证据。

标题第二段为明显地区的两条单位置unknown；不从介绍猜公司。页面实际文本节点“学历/要求”“专业/要求”未与指定精确标签匹配，字段unknown，不用相似标签顶替。附加“经验要求/适用届别/能不能报”等只作分段边界。介绍在操作入口“查看原始公告”前截止，删除后续隐私提示。

真实介绍较短，证据可少于300字，run记录length_warning，不补字、不截断或填充。原始公告href不在白名单时unknown，不发请求追访。采集成功不代表人工验证或可报名。

首次台账robotparser对请求UA计算api_allowed=true，与前次通用规则结论存在差异；未保存该次robots原始规则，不据此推断/api/可采。脚本硬白名单始终禁止/api/。新版本增加robots规则有效性检查、脱敏规则记录与精确间隔测量；不会追溯伪填首次运行未测量的数据。最新解析代码在已有文本与离线测试验证，未为验证而扩大这次3条网络样本。

## 实测验收

- `python scripts/test_collect_jobs.py`：7项通过，覆盖白名单、403/429和连续非200、串行间隔、正文边界、unknown、CSV→现有fixture导入；无网络，无真实统计混用。
- `python scripts/test_data_pipeline.py`：原回归全部PASS。
- `python scripts/import_data.py --input data/raw/AUTO-*.records.csv --check-only`：exit=1；input=3、validated=1、failed=2、processed_written=false。失败是单位unknown触发既有契约，不是偷偷放宽必填条件。
- `python scripts/validate_data.py`：exit=0，production records=0，NO REAL DATA / eligibility not proven提示保留。

## 待人工确认门禁

尚未运行30条，尚未导入processed。请先核对三条字段及证据，并决定是否接受该精确标签策略；需要可导入两条缺单位记录时须提供可核验单位依据，否则维持排除。人工确认之后才允许30条或实际导入；本轮不把“采集3条”写成“生产导入3条”。
