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

2026-10-30：CO-002授权及UA本地配置/日志脱敏确认来自本次用户原文。代码与文档、3条raw预览见任务提交（下一收尾提交登记SHA）；实际网络台账data/raw/AUTO-20261030-2012.run.json。本文及B05A_REPORT仅为过程/验收说明，不冒充原始对话；不改动或复制既有4份native。先抓3条、离线修正，不跑30条、不导入processed。
