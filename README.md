# 职点迷津 AI 求职助手

一个属于自己的 AI 求职助手网站，帮助大学生寻找央国企岗位。

夜间 A→D：10条真实来源候选已导入；本地 Next.js 应用骨架已建立，尚未部署。

本地启动：`npm run build --prefix app`、`npm start --prefix app`，打开 `http://127.0.0.1:3000`。使用与限制见 [应用说明](app/README.md)，验收结果见 [夜间状态](OVERNIGHT_STATUS.md)。

冻结选型见 docs/DECISIONS.md；数据政策见 docs/DATA_SCOPE.md 和 data/GIT_POLICY.md。
单一校验入口：`python scripts/validate_data.py`（B03 建立）。

原始记录 native 本地原样保存，未经人工审查不得推送。人工网页原文补存使用独立通道，不能以摘要替代。
每任务记录真实起止时间；未知耗时写“未测量”。每卡提交后，将 SHA 登记在索引和耗时表，下一提交固化，最后独立收尾。
不提交密钥、真实简历、个人联系方式；原始考题 PDF 留在本地。

