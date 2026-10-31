# 离线规则评测结果

命令：`node --experimental-strip-types eval/run_eval.ts`。仅导入规则函数与本地真实岗位JSON，不调用模型或联网。

按参赛者指定表运行8例，覆盖4个不同的真实岗位（01、02、03、08），不是8个不同岗位。画像均为构造条件，不含真实个人信息。E1确认已有学历，专业省略表示未提供；只有E6为confirmed:false。

| id | job | expect | actual | 是否一致 | 首个unknown字段或fail原因 |
|---|---|---|---|---|---|
| E1 | MANUAL-20261030-220241-01 · 物流部航线运营岗 | ineligible | ineligible | 一致 | education：学历低于明确要求 |
| E2 | MANUAL-20261030-220241-03 · 申能保险管培生（行政方向）（2027届） | ineligible | ineligible | 一致 | education：学历低于明确要求 |
| E3 | MANUAL-20261030-220241-03 · 申能保险管培生（行政方向）（2027届） | unknown | unknown | 一致 | major：专业条件缺失或需要目录口径核实 |
| E4 | MANUAL-20261030-220241-01 · 物流部航线运营岗 | unknown | unknown | 一致 | batch：届别信息缺失 |
| E5 | MANUAL-20261030-220241-08 · 上海国缆试验员（试验工程师）（2027届） | unknown | unknown | 一致 | major：专业条件缺失或需要目录口径核实 |
| E6 | MANUAL-20261030-220241-01 · 物流部航线运营岗 | unknown | unknown | 一致 | profile_confirmation：请先确认求职条件 |
| E7 | MANUAL-20261030-220241-01 · 物流部航线运营岗 | ineligible | ineligible | 一致 | open_status：具体截止日期已经过去 |
| E8 | MANUAL-20261030-220241-02 · 吴忠热电集控巡操（2027届） | unknown | unknown | 一致 | major：专业条件缺失或需要目录口径核实 |

- 判定一致率：8/8 = 100.0%。
- expect为eligible或ineligible的已判定项一致率：3/3 = 100.0%（本表3例均为预期ineligible，无预期eligible）。
- actual为unknown的占比：5/8 = 62.5%。

本次没有不一致项；expect按指定表保留，未为迎合结果而更改。

**本评测只覆盖规则层，不含模型生成质量。** 8例未覆盖所有岗位、条件或边界，也没有证明任何真实用户确定具备报名资格；不将一致率当作模型正确率或全面准确率。

复核输入：[cases.json](cases.json)、[runner](run_eval.ts)、[规则](../app/lib/match.ts)、[真实岗位](../app/lib/jobs.json)。原文溯源见[数据报告](../data/REPORT.md)。

| 输入 | SHA256 |
|---|---|
| cases.json | cfccbfd9654f806ef74196940137c767fc38fa5821daae7dc9533c6f021f259e |
| app/lib/match.ts | 823bf8787504e83003fccd660c07208b7002989c216619be6ccf9384534b88ba |
| app/lib/jobs.json | 83a915ffe9ddfe59da4db8b1905f722959409a9865812c0176b4c218f789904f |
