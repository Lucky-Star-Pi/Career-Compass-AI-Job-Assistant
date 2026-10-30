# 阶段一审查修复验收（实测输出整理，非原始记录）

日期2026-10-30，Asia/Shanghai。本轮未新增依赖或业务功能，未改变资格三态数据语义。四份native仅只读重算，不复制或改写。

## 生产闸门

`python scripts/validate_data.py` exit=0：

```text
PASS: production records=0; NO REAL DATA / eligibility not proven
```

## 离线回归

`python scripts/test_data_pipeline.py` exit=0：

```text
PASS fixture import: unknown; no eligibility inferred
PASS source_url ?id=12345: invalid source_url=False
PASS source_url ?token=abc: invalid source_url=True
PASS source_url #frag: invalid source_url=True
PASS source_url user:pass@: invalid source_url=True
PASS source_url ordinary jobId/from/utm_*: invalid source_url=False
PASS all denied query names, mixed-case and encoded names
PASS missing source_url: child exit=1
PASS missing obtained_at: child exit=1
PASS missing evidence_hash: child exit=1
PASS missing raw_snapshot: child exit=1
PASS missing status: child exit=1
PASS missing missing_fields: child exit=1
PASS fixtures mixed into production input: child exit=1
PASS evidence hash mismatch rejected
PASS dedup retains sources; conflicting evidence queued as unknown
PASS failed import recorded without source content
PASS missing profile and conditions cannot become eligible
PASS ineligible requires evidenced failure
PASS all offline pipeline regression checks
```

## 证据不变性

从Git读取3908689的manifest与当前文件逐字节比较，只替换第4行commit字段；验证输出：

```text
PASS manifest byte diff: only MODEL-CHANGE commit field changed
PASS 20261030-185702-B01.jsonl bytes=586408 lines=153 SHA256=ec4bd6ef97ae07716fe78ddcb98aef7201276f06bed9f612cf867be8d0ce807d
PASS 20261030-191213-STAGE1.jsonl bytes=981551 lines=331 SHA256=3798c1d11ceea90637217a38b9bd8edaca41a46122f5163b7f8928ee5eb7aaf9
PASS 20261030-191705-CLOSURE.jsonl bytes=1052587 lines=369 SHA256=0e747acb504c0491a993035067be109eac21d5b1119200fde1afecb9438f80a9
PASS 20261030-192543-MODEL-CHANGE.jsonl bytes=1176339 lines=442 SHA256=342d5822d32ab565dfb7e4bd35307b124b584c67affe5c624b3f632aa415cdc7
```

占位检查的原始命令和命中内容已在本聊天工具输出留存；结果只有DELIVERY_PLAN.md第31行规则及capture_record.py第31行模板，不命中manifest。此说明不重复占位字符串，以免污染该检查。

## 剩余未交付项

真实岗位仍0条。原始记录尚未实际人工审查/加密交付；本轮仅补齐可执行方案与B18前硬约束，不宣称交付完成。未修改或重写任何已有提交。
