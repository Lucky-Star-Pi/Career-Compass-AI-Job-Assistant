# 数据操作

按COLLECTION_ORDER人工采集，填写raw材料和台账。CONTRACT定义内部字段，不代表网站有这些字段。

虚构链路：`python scripts/import_data.py --input data/fixtures/input.json --fixture`。
人工真实材料准备后：`python scripts/import_data.py --input data/raw/CO-001.records.json`。
真实入口要求显式is_fixture=false；不会自动遍历或访问网站，也不会自动生成合格结论。
真实已有jobs.json时拒绝覆盖，先人工归档和核对，不静默丢弃历史数据。

唯一生产闸门：`python scripts/validate_data.py`。
回归验证：`python scripts/test_data_pipeline.py`。测试在临时目录操作，不向processed写入虚构记录。
fixtures输出始终在fixtures内部，不影响真实统计；机器通过且0条不等于真实数据或推荐能力通过。

CO-002公开采集：先本地配置CAREER_COMPASS_CONTACT（不在聊天或仓库填写邮箱），再`python scripts/collect_jobs.py --limit 3 --dry-run`。该命令真实发请求、写raw，不是模拟；人审后才能跑30条。只遵守工单白名单，无代理、串行、拒绝重定向；失败停止规则不可关闭。

CO-001.records.csv是共享表头空模板，AUTO CSV逐列一致。原始材料核对后先`python scripts/import_data.py --input data/raw/AUTO-*.records.csv --check-only`；通配符须只匹配一个批次，多批次需明确选择文件。预检不写processed；确认后去掉check-only才导入，已有生产输出仍拒绝覆盖。

当前3条预览的修正与未满足项见B05A_REPORT.md；不把CSV解析能力验证写成3条均可导入。

B05-C/CO-003取代原CO-002运行上限：先`python scripts/collect_jobs.py --limit 10 --delay 1.5`，通过代码产出门禁后才允许`--limit 150`。当前未有通过的pilot，150被代码拦截。最终严格CSV不包含unknown招聘类型、未知截止或社招，不把源数据筛选结果当个人eligible。
只读检查可同时读取BATCH-*.records.csv多个批次；实际导入仍要求具体单批且需人工确认。当前各BATCH CSV无入选行，input_empty=true不能当数据验收完成。详情见B05C_REPORT.md。
