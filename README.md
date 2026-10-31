# 职点迷津 · AI 求职助手

## 在线访问

[http://118.89.79.239:3000](http://118.89.79.239:3000)

岗位列表公开，无需登录；与右下角AI助手对话时需要登录，可注册独立账号或使用公开体验账号demo / demo2026（多人共享）。当前样本10条，采集于2026-10-30，全部来自职点迷津公开岗位页；每条附来源URL、获取时间与证据原文。页面上的开放声明不代表个人报名资格通过。列表支持搜索、学历/招聘类型/地点多选与截止排序，无JS也能看到10条岗位。悬浮助手保留最近20条对话与确认画像，支持粘贴简历要点、槽位确认及删除，不支持PDF/OCR。

## 目录

- [docs/SUBMISSION.md](docs/SUBMISSION.md) —— 提交说明（可信性、工时、未完成项）
- [docs/OPS.md](docs/OPS.md) —— 当前实际部署与运维
- [docs/DECISIONS.md](docs/DECISIONS.md) —— 早期技术选型，实际部署变更见OPS
- [docs/DATA_SCOPE.md](docs/DATA_SCOPE.md) —— 数据权限边界
- [data/processed/jobs.json](data/processed/jobs.json) —— 10条结构化岗位；逐条evidence_hash为证据TXT的SHA256
- [data/raw/MANUAL-20261030-220241.pages/](data/raw/MANUAL-20261030-220241.pages/) —— 10份证据原文
- [agent-records/native-manifest.jsonl](agent-records/native-manifest.jsonl) —— 原始协作记录哈希清单；原件未随仓库交付
- [app/](app/) —— Next.js应用
- [scripts/](scripts/) —— 采集、校验、导入脚本（Python标准库）

## 本地开发与历史阶段记录

一个属于自己的 AI 求职助手网站，帮助大学生寻找央国企岗位。

2026-10-30夜间A→D历史状态：10条真实来源候选导入，本地应用骨架建立；当时尚未部署。当前部署以OPS为准。

本地启动：`npm run build --prefix app`、`npm start --prefix app`，打开 `http://127.0.0.1:3000`。使用与限制见 [应用说明](app/README.md)，验收结果见 [夜间状态](OVERNIGHT_STATUS.md)。

冻结选型见 docs/DECISIONS.md；数据政策见 docs/DATA_SCOPE.md 和 data/GIT_POLICY.md。
单一校验入口：`python scripts/validate_data.py`（B03 建立）。

原始记录 native 本地原样保存，未经人工审查不得推送。人工网页原文补存使用独立通道，不能以摘要替代。
每任务记录真实起止时间；未知耗时写“未测量”。每卡提交后，将 SHA 登记在索引和耗时表，下一提交固化，最后独立收尾。
不提交密钥、真实简历、个人联系方式；原始考题 PDF 留在本地。

