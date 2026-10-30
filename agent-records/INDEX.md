# 原始协作记录索引

| 文件 | 任务 | 捕获时间 | 关联提交 | SHA256 | export_method |
|---|---|---|---|---|---|
| raw/native/20261030-185702-B01.jsonl（本地隔离，未入 Git） | B01 | 2026-10-30T18:57:02+08:00 | 499b5e4 | ec4bd6ef97ae07716fe78ddcb98aef7201276f06bed9f612cf867be8d0ce807d | native-byte-prefix-copy |

底座提交：1de9e73。原生快照重开 153 行，哈希一致。隐私人工审查未完成；交付审查见 REDACTION.md，缺失见 MISSING.md。

B02 文档与工单提交：76e8f97；原始工具执行将由本阶段末native快照覆盖，notes不是原始记录。
B03 导入及机器闸门提交：774553c；实测摘要见notes/B03-verification.md。
B04 预备提交：007b903。

| 文件 | 任务 | 捕获时间 | 关联提交 | SHA256 | export_method |
|---|---|---|---|---|---|
| raw/native/20261030-191213-STAGE1.jsonl（本地隔离） | B02/B03/B04 | 2026-10-30T19:12:13+08:00 | 76e8f97 / 774553c / 007b903 | 3798c1d11ceea90637217a38b9bd8edaca41a46122f5163b7f8928ee5eb7aaf9 | native-byte-prefix-copy |

第二快照331行，重开哈希一致；覆盖到捕获前的真实过程，不含捕获后的报告与push。

| 文件 | 任务 | 捕获时间 | 关联提交 | SHA256 | export_method |
|---|---|---|---|---|---|
| raw/native/20261030-191705-CLOSURE.jsonl（本地隔离） | 阶段报告/首次push | 2026-10-30T19:17:05+08:00 | 64f7996 | 0e747acb504c0491a993035067be109eac21d5b1119200fde1afecb9438f80a9 | native-byte-prefix-copy |

阶段报告提交64f7996；首次push成功。CLOSURE后审计及最终回复未包含，不以摘要补造。最后审计提交本身可由Git历史定位。


MODEL-CHANGE (2026-10-30): agent-records/raw/native/20261030-192543-MODEL-CHANGE.jsonl | 2026-10-30T19:25:43+08:00 | SHA256 342d5822d32ab565dfb7e4bd35307b124b584c67affe5c624b3f632aa415cdc7 | native-byte-prefix-copy | commit: 3908689; local only, privacy review pending.

## 阶段一审查修复

| 任务 | 关联commit | 记录 |
|---|---|---|
| D1/D2主体/D7/D8 | 4d5e018；清单/耗时字段及P00补正在本轮收尾提交 | 三段推送及历史SHA；没有改动native |
| D3 | dc2b3b8 | DELIVERY_PLAN.md；原件/副本尚未制作或交付 |
| D4/D6 | e10ce5f | 离线校验与新URL用例实测通过 |
| 独立收尾 | 由Git历史中chore: record repair SHAs in index and timelog定位 | 本表、TIMELOG和报告修复记录；不回填自身SHA |

实测摘要：notes/REPAIR_VERIFICATION.md，属于验收说明，不是原始对话。按本轮指令未复制、裁剪或重写任何native；本轮原始过程不在既有4份快照内，不能以本说明冒充原文。

## B05-A 有限采集预览

2026-10-30：CO-002授权及UA本地配置/日志脱敏确认来自本次用户原文。代码与文档、3条raw预览任务提交c58c86f；实际网络台账data/raw/AUTO-20261030-2012.run.json。本文及B05A_REPORT仅为过程/验收说明，不冒充原始对话；不改动或复制既有4份native。先抓3条、离线修正，不跑30条、不导入processed。索引收尾提交自身由Git历史定位。

## B05-C 有限扩量与时间筛选

2026-10-30追加授权原文在本聊天；实际过程见5份BATCH run.json及data/B05C_REPORT.md。41个不同详情、71请求，严格入选0；最终10页失败，未运行150。没有保存HTML、没有改动native或processed。上述报告是验收说明，不冒充原始对话；任务提交6e639cb；紧接收尾提交固化关联，本收尾自身SHA以Git历史定位。

## B05-G 人工通道

本地候选22条：优先0、备选3、不看19；9项测试通过，空表0行和SAMPLE拒绝均已实际运行。人工选择稍后填写，真实首条与15条验收尚未完成；未请求网站、未写processed。报告data/B05G_REPORT.md；任务提交c30b9dc，紧接H提交固化关联。保留其他B05-E及本人已有工作，不混入该任务提交。

## B05-H 人工URL清单

本人提供15非空行，规范化选10/跳过5；MANUAL-20261030-220241批次仅10个详情GET，10成功、0失败、34个PENDING；未填合并实际拒绝10行。元数据和人工核对表见data/MANUAL-20261030-220241.REPORT.md。6项H测试和9项G回归通过，补齐合并仅用临时合成输入验证，不冒充10条真实已人工核验。未读会话、未触碰native、未写processed；任务提交dfdc631；紧接收尾提交固化关联，收尾自身以Git历史定位。

## B05-I 布局A/B离线修复

10份证据SHA256与H原网络台账一致；旧auto/FILL_ME/run完整保留.v1。新run模式reparse、requests=0；10条国企原文定位、1具体截止2027-01-25、9显式长期招聘、学历10有值、FILL_ME剩1个PENDING。只读合并通过9/拒绝1；未导出或写processed。说明见data/MANUAL-20261030-220241.REPARSE.md；任务提交SHA在紧接收尾登记。没有复制或改动native，验收说明不冒充原始记录。
