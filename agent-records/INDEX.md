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

本人提供15非空行，规范化选10/跳过5；MANUAL-20261030-220241批次仅10个详情GET，10成功、0失败、34个PENDING；未填合并实际拒绝10行。元数据和人工核对表见docs/reports/MANUAL-20261030-220241.REPORT.md。6项H测试和9项G回归通过，补齐合并仅用临时合成输入验证，不冒充10条真实已人工核验。未读会话、未触碰native、未写processed；任务提交dfdc631；紧接收尾提交固化关联，收尾自身以Git历史定位。

## B05-I 布局A/B离线修复

10份证据SHA256与H原网络台账一致；旧auto/FILL_ME/run完整保留.v1。新run模式reparse、requests=0；10条国企原文定位、1具体截止2027-01-25、9显式长期招聘、学历10有值、FILL_ME剩1个PENDING。只读合并通过9/拒绝1；未导出或写processed。说明见docs/reports/MANUAL-20261030-220241.REPARSE.md；任务提交b75f99d，紧接收尾提交固化；收尾自身以Git历史定位。没有复制或改动native，验收说明不冒充原始记录。

## 夜间 A→D 验收索引

A：53939a2；B：f56c971；C：0cad7c5；D：本节所在提交（由Git历史定位，避免自身SHA循环）。报告OVERNIGHT_STATUS.md与data/IMPORT_REPORT.md为验收说明，export_method=verification-note，不是原始记录。未读取、复制、改写native，未补造聊天原文；本轮原始导出仍需人工按DELIVERY_PLAN交付，缺口不以本节摘要替代。10份证据SHA256列于OVERNIGHT_STATUS，关联raw/processed/app只读副本可复核。迁移后的历史报告路径已同步。

## 2026-10-31 Chat截断修复

| 文件 | 任务 | 验收记录时间 | 关联提交 | SHA256 | export_method |
|---|---|---|---|---|---|
| docs/reports/CHAT_TRUNCATION_FIX.md | CHAT-TRUNCATION | 2026-10-31T09:48:16+08:00 | 6d1bbf9 | 5dfbb22dedf1f46363aa397bae02bc56931c29748914c550e288508a72d8f3ce | verification-note |

实测17项测试全绿、中文路径构建通过、真实接口连续3次connected=true。受限环境首次降级也已在报告披露。未读取/复制/改写native，本节不替代原始协作记录；原件交付仍按DELIVERY_PLAN执行。本次验收记录收尾提交自身由Git历史定位。

## 2026-10-31 容器构建配置

仅新增容器配置、修改start及同步本地启动说明；未构建镜像、部署或push。以下为文件校验索引，非协作原文；本次提交由Git历史中chore: add container build for domestic hosting定位，自身SHA不循环回填。

| 文件 | 任务 | 时间 | 关联提交 | SHA256 | export_method |
|---|---|---|---|---|---|
| app/Dockerfile | CONTAINER-BUILD | 2026-10-31T10:01:08+08:00 | 本条所在提交 | 44c857ee70bbb8ea02b0c52b2334ed5a50c77dc1f6b16d49d15eb6c90a4325c2 | verification-note |
| app/.dockerignore | CONTAINER-BUILD | 2026-10-31T10:01:08+08:00 | 本条所在提交 | e96ac69d8a19bf70ae4e0dc3a8744c66110f2a919cccead594f8240a79950e82 | verification-note |
| app/package.json | CONTAINER-BUILD | 2026-10-31T10:01:08+08:00 | 本条所在提交 | dd8c73335fca777c11f0660231a60943830041fafabd065b5c63e87ee40abb81 | verification-note |
| app/README.md | CONTAINER-BUILD | 2026-10-31T10:01:08+08:00 | 本条所在提交 | afb8fae548b5939e6101379cbfdc53230b0c224fbdb172605fdabb2d73abf9c4 | verification-note |

## 2026-10-31 状态同步与提交材料

采用审阅方确认的实现和本人核对数据：UI提交0601c8a、10条核对标记提交8f2deb3；文案提交53d3c4c。两份jobs.json已转LF且字节相同；来源核对不等于个人资格eligible。P0-1提交前diff仅五个指定文件；此后文案与材料独立提交。按参赛者要求不重复其已验证的测试/构建/线上对话。

GitHub:443直连push在本次执行环境多次失败，包含参赛者报告网络恢复后的重试；未因此改系统代理/hosts/服务器文件，未把本地SHA写成已发布线上SHA。后续若push成功，以实际工具结果及站点文案核验追加记录。

| 文件 | 任务 | 记录时间 | 关联提交 | SHA256 | export_method |
|---|---|---|---|---|---|
| README.md | P0-3 | 2026-10-31T11:43:18+08:00 | 本材料提交（Git历史定位） | ceb43ad5b6cc13625171792f227915e9153a3ee1e6b991e1ddcac35c6d70502a | verification-note |
| docs/SUBMISSION.md | P0-3 | 2026-10-31T11:43:18+08:00 | 本材料提交（Git历史定位） | 65f391fdb16a5f5a4f306099df34be4ee475653d7c4dd2fa79cbc5a8504eccee | verification-note |
| docs/OPS.md | P0-3 | 2026-10-31T11:43:18+08:00 | 本材料提交（Git历史定位） | b66303e0ae334e034041d8c6122bc248553fec75e5836347396dec7621cee7a2 | verification-note |
| TIMELOG.csv | P0-3 | 2026-10-31T11:43:18+08:00 | 本材料提交（Git历史定位） | ff3e34796658e0e27d8ac5cec67101ea13730ca60a0067393990fbfa453a4251 | verification-note |

以上为提交材料/验收索引，不是协作原始记录。本轮未读取、复制或修改native原件，四份原件仍未随仓库交付；脱敏副本也未制作。阶段窗口仅记录在TIMELOG备注，未观测时长未补造。

## 第四轮阶段A

f94ed61：账号与隔离存储。实际输出19测试全绿、build exit0，check_accounts.py的匿名401/demo登录/双账号隔离/跨会话/重启持久化/退出全部PASS。已push，等待90秒线上匿名me401、首页跳login、demo登录与账号读取200。用户数据仅在应用目录外；本次只有合成测试数据，未读或改native。验收摘要export_method=verification-note，不冒充原文。

## 第四轮阶段B与C预检

B提交82549fd，浏览器发现Origin校验误拒后以9203f05修正；19测试、类型与构建均通过，重新验证demo浏览器登录、消息持久化刷新和岗位原文展开成功；已独立push。第一次线上探测早于90秒不计通过；超过90秒仍为A页面，线上发布未确认，已请参赛者查看部署日志。C本地24测试与类型检查通过，模型槽位仅作待确认建议，简历原文不进入消息/缓存。C构建与真实调用将在实际完成后补记。均为verification-note，不冒充协作原始记录。

## 第四轮C验收收尾

C：a7ee54d、fb62a48、25816de；24测试、类型、构建、真实模型3场景与本机浏览器确认/追问/合成简历/删除通过，详见docs/reports/R4_REPORT.md。B线上在12:59:21+08:00确认更新后才准备独立push C。第二会话隔离用独立Cookie客户端验证，不伪称第二浏览器GUI实测。原文、密码、Cookie未写入验收材料；不改native；export_method=verification-note。本节提交自身由Git历史定位，线上C结果以随后真实工具输出为准。

## 第六轮公开列表与悬浮助手

C在途已由402b399保存并push，本轮起点干净。R6本地实际结果见docs/reports/R6_REPORT.md；报告SHA256=262149333c5c769e015dfb48663c4e6d64ae8b37600291afb9aa0df754435bfa；记录时间=2026-10-31T13:18:43+08:00；export_method=verification-note；关联本轮唯一提交feat: job list first with floating assistant（自身SHA由Git历史定位）。未修改native、账户文件或规则，未新增依赖；本轮不包含真实简历/密码，不将降级当模型成功。线上发布结果以随后90秒核验的实际工具输出为准。

## 提交文档与现状对齐

记录时间：2026-10-31T13:35:17+08:00；任务SUBMISSION-SYNC；本任务提交docs: align submission with login, resume and deployment reality由Git历史定位。只修改说明和真实耗时索引，应用功能基线仍为a6a9854；16:00为参赛者指定统计口径，09–16分段自报未逐段计时，不伪造工具观测。指定grep无命中，六节/六条可信机制及链接检查通过；export_method=verification-note，不替代原文。

- docs/SUBMISSION.md SHA256=17ee40af795c4d41bf6ff0c93bdeb8addcbdae652466e86c62ba76001e765ab1
- README.md SHA256=2448f047443699e3ba3887ee5bc1764d49f17be5aa31a48534559a3b67824ed2

## 第七轮小职验收

记录时间：2026-10-31T14:16:52+08:00；任务R7-XIAOZHI；文件docs/reports/R7_REPORT.md；SHA256=9d0d73a47a57eb4d65851a86b822038d3f1a9ac416718f67906923ac9d0af18f；export_method=verification-note；关联本轮功能提交（自身SHA由Git历史定位）。构建、35测试、账号/数据回归、错误Key转规则及浏览器合成PDF/气泡验收通过；Qwen成功层仅模拟验证，未称真实调用。原始native未读取或变更，截图/合成运行数据仅本地忽略区；本段不替代原始协作记录。

## 回答校验误杀修复

记录时间：2026-10-31T14:35:02+08:00；任务REPLY-GUARD；文件docs/reports/REPLY_GUARD_REPORT.md；SHA256=ed95a2d258fb9cebfb1bd5b293b229112814b7e51cd2cf2aa715f75209dc3986；export_method=verification-note；关联本轮fix提交（自身SHA由Git历史定位）。36测试/build/类型/10条数据校验通过，三条真实DeepSeek请求和错误Key转rules通过；首次问题3仍降级已如实记载。原件未读取或修改；此材料不是原始对话导出，线上验收以后续90秒工具结果为准。

## 模型结构化事实修复

记录时间：2026-10-31T14:52:23+08:00；任务MODEL-EVIDENCE；文件docs/reports/MODEL_EVIDENCE_REPORT.md；SHA256=bc3ea96366113003f3bd5188d21d7522858bceafdde01eb80d04098918f9a389；export_method=verification-note；关联本轮fix提交（自身SHA由Git历史定位）。38测试/build/类型/10条数据校验通过；三问真实DeepSeek正确给出01湛江和03硕士，已记录初次降级及提示词调整。原件未读取/修改，记录不冒充原始协作导出；线上实际结果见后续90秒工具输出。
