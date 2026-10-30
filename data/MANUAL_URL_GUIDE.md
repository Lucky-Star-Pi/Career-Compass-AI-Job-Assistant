# B05-H 人工URL清单抓取与合并

授权：参赛者2026-10-30 B05-H，仅抓本人提供的/jobs/<uuid> URL，不请求筛选列表、sitemap、robots、API或公告站。本阶段覆盖B05-G的“纯离线”执行范围，只为该有限详情清单增加读取。匿名，无Cookie，不读取会话或用户账户文件。

1. 本人在data/raw/MANUAL_URLS.txt逐行复制详情URL。脚本去掉query/fragment后严格比对https://www.zhidianmijin.com.cn/jobs/和36位小写十六进制/连字符。去重、最多30条；非法/重复/超额行逐项报告，非法原文不落日志。
2. 本地配置CAREER_COMPASS_CONTACT，再运行`python scripts/collect_manual_urls.py`。每次串行，完成后间隔≥1.5s，不重试、不跟随重定向；403/429或连续2次非200停止，风控/验证码也立即停。不会自动发现新URL或从索引补数。
3. 输出MANUAL-时间.pages/NN.evidence.txt、28列auto.csv、固定10列FILL_ME.csv、run.json，以及data/MANUAL-时间.REPORT.md。成功产出与HTTP200分开统计；失败无伪造的自动记录。

## 三态

- 具体值：详情可见原文支持的字段；不凭单位名推性质、不从发布日期推报名开始。
- unknown：详情明确未写，或完整目标段中没有该字段迹象；不等于不限。
- PENDING：仍须人工确认、存在字段迹象却无法可靠抽取、岗位/单位未定位、单位性质、开放状态、核验备注等。

具体截止日即使可见也留PENDING，不能由脚本替人确认；详情明确未写则unknown。报名开始没有显式字段保持unknown，有待核的源日期留PENDING，不从其他日期推算。

FILL_ME仅有：编号、岗位名称、单位名称、详情页URL、公告URL、报名开始、报名截止、开放状态、单位性质、备注。若其他列仍PENDING，报告会列出，需要本人在完整28列auto表补原文证据后填写；不擅自增加FILL_ME列或把歧义改成unknown。

## 人工合并

`python scripts/manual_intake.py --input data/raw/MANUAL-时间.FILL_ME.csv --auto data/raw/MANUAL-时间.auto.csv --check-only`

以编号匹配，人工10列覆盖自动表，编号集合必须一致，不静默丢行。PENDING在任何列残留即拒绝；把原PENDING清空仍按PENDING拒绝。本人显式填unknown表示已核实未写，不是脚本自动转换。日期、URL、重复证据、PII、原文逐字等沿用G。

证据继承BATCH前三行（岗位名/URL/获取时间），增加第四行公告URL作为来源元信息；普通G仍用其手工四行头，--auto仅额外接受该采集四行头。原文正文不重写。本人新增公告URL或更正岗位名时须同步补充该岗证据元信息及获准保存的真实原文；脚本不会伪造已抓过公告的证明。公告链接即使自动识别也只列在核对清单，不发请求。

全部通过后去掉check-only，仅写raw/MANUAL.records.json和MANUAL_REPORT.md。任何拒绝时不导出部分记录。人工另行确认前，不执行import_data.py实际导入，不写processed。

本轮先前的B05-E文件及本人已有save_session.py均保留，H不调用或提交这些会话代码。原始URL清单可能包含附带参数，保留本人原文件，不自动重写；日志与产物只使用去参数后的规范详情URL。
