# 持续记录

1. 每卡开始记录 Asia/Shanghai 实际时间。结束时记录实际结束；未观测的人工/等待耗时填“未测量”，不得倒推。
2. 使用 `python scripts/capture_record.py <本次源jsonl路径> --task B01` 捕获完整行前缀；脚本不访问网络、不输出正文。
3. 重开本地目标验证 JSONL 可解析，核对 native-manifest.jsonl 的 SHA256。源文件增长不影响既有快照。
4. 原件保留在 raw/native，本地隔离；脱敏审查通过前不加入 Git 或提交包。
5. 人工网页记录放 raw/YYYYMMDD-HHMM-NN-task.md，头部逐项填写 captured_at、tool、model、task_id、prompt_sha256、commit、export_method=manual-paste。正文必须粘贴原文；没有原文则不创建记录。
6. 提交后索引填写该任务 SHA，下一次提交固化。任务提交不能包含其自身 SHA；最终审计登记提交的 SHA 由 Git 历史定位。
7. TIMELOG 增加关联提交列；墙钟为结束减开始，其他指标仅按实测填写。
8. manifest 的待提交占位值（capture_record.py中的模板值，具体见DELIVERY_PLAN）必须在紧接着的下一次提交内消除，否则视为未完成；收尾提交自身SHA由Git历史定位，不强行回填。
