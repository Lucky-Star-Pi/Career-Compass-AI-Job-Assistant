# 夜间任务状态

记录时间：2026-10-30T23:03:22+08:00。本轮完成即停，不部署、不push、不访问岗位/公告网站、不进行付费模型调用。

## A / B / C / D

| 任务 | 结果 | 提交与证据 |
|---|---|---|
| A 数据质量 | 10条引用逐字匹配；UI排除；01公告/经验unknown，证书保留原句；03/05学历要求下一行均为硕士 | 53939a2；scripts/night_quality.py |
| B 合并导入 | 10通过/0拒绝，processed真实10条；status全部unknown，来源人工复核pending | f56c971；data/IMPORT_REPORT.md |
| C 文档整理 | 六份主文档移至docs，历史报告至docs/reports，v1至raw/archive；证据路径不变；提交后三项回归全绿，无需revert | 0cad7c5；本轮收尾补齐历史索引的纯文本路径 |
| D 应用骨架 | Next15/TS5/Tailwind；只读JSON；保守三态纯函数；条件签名Cookie；受限问答及无Key降级 | 本文件所在D提交，以Git历史定位 |

## 验收命令与实际结果

- `python scripts/validate_data.py` → `PASS: production records=10`。
- `python scripts/test_data_pipeline.py` → `PASS all offline pipeline regression checks`。
- `python scripts/manual_intake.py --check-only` → `通过=10 拒绝=0 A档(open)=10 check_only=True`。这里open是页面声明，不代表用户eligible。
- `npm test --prefix app` → tests 9 / pass 9 / fail 0。
- `npm run build --prefix app` → exit=0；首页与3个API路由产物生成，当前中文路径构建通过。首次TS7不兼容失败，固定TS5后通过；未迁移目录。
- `python app/scripts/smoke.py` → health10/模型未接通、首页HTTP200、签名Cookie往返/防篡改/身份字段拒绝、无Key降级、清除条件全部PASS。测试进程主动移除模型Key，无付费调用。
- app/lib/jobs.json与data/processed/jobs.json字节相同；10份TXT与夜间前1993103版本逐字节相同。

## 10条最终字段

个人资格status全unknown；备注可空、其他列零PENDING。完整28列及条件原文分别见data/raw/MANUAL.csv与data/processed/jobs.json。

| 编号尾号 | 岗位 | 单位 | 性质 | 学历 | 专业 | 报名截止/开放声明 | 新引用 | status |
|---|---|---|---|---|---|---|---|---|
| 01 | 物流部航线运营岗 | 广州中远海运物流供应链有限公司 | 国企 | 本科 | 经济与贸易类、国际商务类、交通运输类、物流管理与工程类、水上运输类 | 2027-01-25 | 本科 | unknown |
| 02 | 吴忠热电集控巡操（2027届） | 申能吴忠热电有限责任公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |
| 03 | 申能保险管培生（行政方向）（2027届） | 申能财产保险股份有限公司 | 国企 | 硕士 | unknown | 长期招聘，无固定截止日期 | 硕士 | unknown |
| 04 | 申能保险分公司管培生（业务发展方向）（2027届） | 申能财产保险股份有限公司陕西省分公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |
| 05 | 申能保险管培生（科创方向）（2027届） | 申能财产保险股份有限公司 | 国企 | 硕士 | unknown | 长期招聘，无固定截止日期 | 硕士 | unknown |
| 06 | 申能保险分公司管培生（业务发展方向）（2027届） | 申能财产保险股份有限公司湖北省分公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |
| 07 | 申能保险分公司管培生（综合管理方向）（2027届） | 申能财产保险股份有限公司浙江省分公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |
| 08 | 上海国缆试验员（试验工程师）（2027届） | 上海国缆检测股份有限公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |
| 09 | 申能保险分公司管培生（综合管理方向）（2027届） | 申能财产保险股份有限公司广东省分公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |
| 10 | 申能保险分公司管培生（综合管理方向）（2027届） | 申能财产保险股份有限公司厦门分公司 | 国企 | 本科 | unknown | 长期招聘，无固定截止日期 | 本科 | unknown |

## 不变证据SHA256

| 文件 | SHA256 |
|---|---|
| 01.evidence.txt | f9115f4a9e437957109912e56b4c821b9da949bece7a37a3fe7486448cb14880 |
| 02.evidence.txt | 9b4be9df6d1d1d61fd044093e64f91e963d40ce3263d1b0b7e0d48d399519cfe |
| 03.evidence.txt | 4cb49ec4ec8ae07b93a728b3534cc0fb0624fa40cbe91794770a52e24c395925 |
| 04.evidence.txt | 14f9b1f4be515e5bf00655349d2cff24cea877937d839e83452d28993e781cc3 |
| 05.evidence.txt | 438fd0d7b66a4981e3d3ab9aa2b01a9f1f017585a0bebf5513ee320c70cde81b |
| 06.evidence.txt | b963c09766823f61dff7112a6c642bcb3ecedc14e404ab232daa4b74d96b80ff |
| 07.evidence.txt | 794bff349bd6d1917f4a833e2dfc9da49c75e3e12a30a277470dae35de45a615 |
| 08.evidence.txt | 5e075de85bc86f74368a1eff286061a3aa4b2e98768544150c6ff5d53e9bb47c |
| 09.evidence.txt | 53b3af3dfca6da6f87f88cef3f897b2621cf6d621b4d41b82abed7726fc1c232 |
| 10.evidence.txt | a45100d79872b75cec95fd6b48aaec14b5333928a4bf3568cdeeaa33847214b9 |

## 未完成与明早第一件事

模型真实调用、余额与告警、稳定Cookie签名密钥、简历、多轮历史、数据库、公网部署与7天可用均未验收。本机缺Key测试明确显示“未接通”；若外部配置Key，实际接口只在成功并通过来源校验后显示调用成功。当前模型50次上限仅单进程内存，不能代替总预算控制。Cookie未配置稳定密钥时重启失效；仅条件枚举，不保存简历、姓名或联系方式。规则不支持的附加条件保持unknown，不将现有10条宣称可报名。模型自由文本事实仍需人工评估，引用校验不能证明每句结论。

明早第一件事：参赛者先本机打开应用，逐条核对10条来源、03/05硕士与长期招聘声明；确认画像→规则解释→清除条件路径。再由本人配置稳定签名密钥与模型Key并核对额度，另行授权最小真实模型测试及部署。当前不消耗付费额度。

保留任务开始前的B05-E代码/个人辅助文件，未混入夜间提交；工作区因此不宣称全干净。原始会话原件仍按既有交付方案人工审查，本报告不冒充原始记录。
