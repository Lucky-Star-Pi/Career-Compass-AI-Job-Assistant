# 数据操作

按COLLECTION_ORDER人工采集，填写raw材料和台账。CONTRACT定义内部字段，不代表网站有这些字段。

虚构链路：`python scripts/import_data.py --input data/fixtures/input.json --fixture`。
人工真实材料准备后：`python scripts/import_data.py --input data/raw/CO-001.records.json`。
真实入口要求显式is_fixture=false；不会自动遍历或访问网站，也不会自动生成合格结论。
真实已有jobs.json时拒绝覆盖，先人工归档和核对，不静默丢弃历史数据。

唯一生产闸门：`python scripts/validate_data.py`。
回归验证：`python scripts/test_data_pipeline.py`。测试在临时目录操作，不向processed写入虚构记录。
fixtures输出始终在fixtures内部，不影响真实统计；机器通过且0条不等于真实数据或推荐能力通过。
