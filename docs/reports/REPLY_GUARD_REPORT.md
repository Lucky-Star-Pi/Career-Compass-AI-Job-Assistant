# 回答校验收窄验收

本轮提交消息：`fix: narrow reply guard so valid answers are not discarded`，自身SHA由Git历史定位。本文件在push前记录本地结果；线上问题1/3在push后至少90秒另行实测，不把本地结果冒充线上结果。

## 修复范围

- chat-output.ts按参赛者指定的上下文正则拦截报名/录用承诺，不再因孤立的“一定”“保证”“无需核实”拒绝普通回复；通用问题允许references=[]。非空引用仍必须ID/URL成对且属于候选，最多5条，仍拒绝status、reply内URL和达到300字的回复。
- route.ts接受层按指定收窄为直接报名/符合全部报名条件/确保录取；PII、原文回显、提示词和规则均保留。
- 首次真实验收问题1/2已转deepseek，但问题3仍rules。发现原来的“推荐”子串检查会把“无法推荐”“不能推荐”等否定说明当正向推荐，增加hasRecommendationClaim仅移除限定的否定短语；混合回复里剩余的正向推荐仍需canRecommend核验。补单测验证该边界；不改match.ts或岗位数据。

## 真实验收结果

命令：`python app/scripts/check_reply_guard.py`。同一个隔离账号按1→2→3顺序请求；错误Key用第二个本机进程验证，不改.env.local或线上配置。合成账号凭据不打印、不写入Git，账号文件在应用目录外的忽略目录，脚本结束自动停止进程。

| 场景 | HTTP | mode | 耗时 | 引用 |
|---|---|---|---|---|
| 1 央国企校招一般什么时候开始 | 200 | deepseek | 1.61秒 | 0 |
| 2 这个岗位我能报吗 | 200 | deepseek | 1.13秒 | 0 |
| 3 2027届本科、国际商务类、意向湛江 | 200 | deepseek | 1.39秒 | 1 |
| 无效DeepSeek Key且Qwen未配置 | 200 | rules | 0.24秒 | 3 |

问题3返回education=本科、major=国际商务类、city=湛江市、graduationYear=2027的待确认槽位。三条模型回复均无报名承诺且不足300字；非空引用全部通过本地10条候选ID与来源URL配对检查，模型未返回status字段。无效Key回复为“小职正在升级中，先用规则结果帮你核对：”加三条规则结果；不称真实模型成功。本轮未实测Qwen账户，不修改或披露任何真实密钥。

## 回归结果

- npm test --prefix app：tests=36，pass=36，fail=0。
- npm run build --prefix app：中文路径exit=0。
- node app/node_modules/typescript/bin/tsc --noEmit --project app/tsconfig.json：exit=0。
- python scripts/validate_data.py：PASS: production records=10。
- 规则核心、两份岗位JSON和native证据未改；未新增npm依赖。

## 发布验收入口

`python app/scripts/check_reply_guard.py --online`注册全新合成测试账号，仅顺序执行问题1和3，并输出HTTP、mode、耗时、引用数量与无敏感信息的回复。调用前须确认push完成并已等待至少90秒；不会改线上环境变量，也不读取现有账号、简历或Cookie。实际输出见本轮随后工具记录。
