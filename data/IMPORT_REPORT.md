# 夜间 B 导入报告

真实导入10条，全部status=unknown：尚无用户画像确认。没有网络采集或模型调用。

| 编号 | 岗位 | 学历 | 截止声明 | status |
|---|---|---|---|---|
| MANUAL-20261030-220241-01 | 物流部航线运营岗 | 本科 | 2027-01-25 | unknown |
| MANUAL-20261030-220241-02 | 吴忠热电集控巡操（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-03 | 申能保险管培生（行政方向）（2027届） | 硕士 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-04 | 申能保险分公司管培生（业务发展方向）（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-05 | 申能保险管培生（科创方向）（2027届） | 硕士 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-06 | 申能保险分公司管培生（业务发展方向）（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-07 | 申能保险分公司管培生（综合管理方向）（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-08 | 上海国缆试验员（试验工程师）（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-09 | 申能保险分公司管培生（综合管理方向）（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |
| MANUAL-20261030-220241-10 | 申能保险分公司管培生（综合管理方向）（2027届） | 本科 | 长期招聘，无固定截止日期 | unknown |

## 缺失字段统计

- age：10/10
- announcement_url：1/10
- application_end：9/10
- application_start：10/10
- application_url：10/10
- batch：1/10
- certificates：9/10
- degree：10/10
- experience：10/10
- graduation_time：10/10
- last_verified_at：10/10
- major：9/10
- notes：10/10
- other_restrictions：10/10
- political_status：10/10
- profile_version：10/10
- status：10/10

实际验收：manual_intake.py --check-only通过10/拒绝0；import_data.py输出input10/output10/failed0/eligible0；validate_data.py输出PASS: production records=10。
证据TXT未修改，01公告unknown、工作经验unknown；证书从介绍原句保留，03/05学历为标签下一行的硕士。
