# B03 实测摘要（不是原始对话记录）

2026-10-30，Asia/Shanghai。原始工具输出由后续native快照覆盖。

`python scripts/import_data.py --input data/fixtures/input.json --fixture` exit=0：mode=FICTIONAL_FIXTURE,input=1,output=1,failed=0,deduplicated=0,review=0,eligible=0。

`python scripts/test_data_pipeline.py` exit=0：
- 六个必需字段逐一删除，实际子进程均exit=1：source_url/obtained_at/evidence_hash/raw_snapshot/status/missing_fields。
- fixtures混入生产输入，实际子进程exit=1。
- 哈希篡改拒绝、重复合并保留来源、冲突入队unknown、失败记录、未知不能eligible、无失败依据不能ineligible均通过。

`python scripts/validate_data.py` exit=0：`PASS: production records=0; NO REAL DATA / eligibility not proven`。

没有真实岗位。空数据闸门通过不等于B03真实采集核验通过。未安装依赖。
