# 内部岗位数据契约 v1

这是产品内部结构，不是对职点迷津实际页面或接口的描述。UTF-8 JSON数组；一条记录对应一个可识别的岗位/批次/地点组合。

所有下列键必须存在；选填表示值可为字面量`unknown`，不代表键可删。没有写明的要求不得标准化为“不限”。明确不限必须带原文证据。

| 字段 | 值与必填性 | 缺失/证据处理 |
|---|---|---|
| id | 必填，内部稳定字符串 | 人工ID或组合键哈希，不假定来源ID |
| name, employer, batch, location, organization_type | name/employer必填，其他选填 | 缺失unknown；单位性质需依据 |
| source_url | 必填，职点迷津公开http(s) URL | 允许普通查询参数（如id、jobId、from、utm_*）；禁止fragment和URL内嵌用户名密码；查询参数名经URL解码后按大小写不敏感拒绝token、access_token、key、api_key、apikey、secret、session、auth、sign、signature、password、pwd、ticket；来源不能虚构 |
| announcement_url, application_url | 选填URL | 无原始公告或报名入口=unknown |
| obtained_at, last_verified_at | 前者必填ISO8601显式+08:00，后者选填同格式 | 核验与获取不同，未核验unknown |
| published_at, application_start, application_end | 选填对象或unknown | 对象至少含raw/normalized/precision；本项目日期时区+08:00，可显式记timezone；仅日期不补具体时刻 |
| education, degree, major, graduation_time, experience, political_status, certificates, age, other_restrictions | 选填对象或unknown | 对象含raw/normalized/evidence_ref；所有实际条件均需覆盖，年龄含基准日，专业含口径 |
| conditions | 必填数组，可空 | 每项field/raw/normalized/logic/evidence_ref；logic保留AND/OR及例外；无法表达进入冲突队列 |
| condition_text | 必填非空脱敏原文 | 不能用模型生成句子替代原文；需在证据TXT中出现 |
| standardized_values, logical_relationships | 必填对象/数组 | 保留标准化值及逻辑，空集合表示尚未完成，不表示无限制 |
| human_verification | 必填对象state/verified_at/evidence_refs | state=pending/verified/conflict；其余无值unknown/[] |
| open_status | 必填枚举open/closed/not_started/unknown/conflict | 缺失或过旧不得认定open |
| open_basis, display_deadline, field_evidence | B05-I新增；开放依据、展示文案、逐字段原文定位 | 具体日期≥2026-10-31可open；页面显式“长期招聘，无固定截止日期”可open但application_end必须unknown、open_basis=长期招聘，展示原句；公告未写明仍unknown。field_evidence包含raw_snapshot/line/raw/evidence_ref原文，不能以长期招聘伪造日期 |
| raw_snapshot | 必填相对路径 | 指data/raw下脱敏TXT证据，非HTML；fixture只能指data/fixtures |
| evidence_hash | 必填64位小写SHA256 | 对raw_snapshot实际字节计算，不证明源内容真实性 |
| evidence_excerpt | 必填非空脱敏片段 | 必须逐字出现在TXT内；原文被脱敏时统一使用相同标识 |
| evidence_metadata | 必填对象url/obtained_at/http_status/screenshot_path | 无法观测HTTP/截图填unknown；URL/时间与记录一致 |
| source_refs | 必填非空数组 | 每项source_url/obtained_at/raw_snapshot/evidence_hash，去重保留所有出处 |
| missing_fields | 必填字符串数组 | 所有unknown顶层字段必须列入；关键条件缺失不得为空 |
| conflicts | 必填数组 | 每项字段、两侧证据、原因；非空则人工复核 |
| status | 必填eligible/ineligible/unknown | 是针对特定画像的资格结论，不是岗位自身属性 |
| evaluations | 必填数组 | 每项field/result/evidence_ref/profile_fact_ref；result=pass/fail/unknown |
| profile_confirmed, profile_version | 必填布尔/字符串 | 本阶段无用户画像，false/unknown |
| is_fixture | 必填布尔 | 真实false；虚构true，永不进入processed |

## 三态与导入门禁

- eligible：已确认特定画像；开放状态及证据有效；全部适用硬条件评估pass，且无缺失/冲突。数据导入器本阶段绝不产生eligible；B06才实现完整资格引擎。
- ineligible：至少一项有证据的明确fail，记录原因及画像事实。公告已截止应排除可报名集合，但没有画像时仍不伪造个人不符结论。
- unknown：无已确认画像、关键未知、无法解析逻辑或冲突；永不显示可报名。
- 本阶段真实导入一律unknown；保留原输入评价但不能未经核验放行。匹配不是清洗器职责。

B05-I（2026-10-30）覆盖先前“无固定截止一律不可open”的开放口径，但不放宽个人资格：长期招聘必须有对应报名截止标签下的显式原句证据；缺截止的普通open仍拒绝。备注可空，不作为PENDING。open仅是页面时点声明，不保证招聘方不变更；现阶段status仍unknown、profile_confirmed=false，未实现的界面须按display_deadline展示长期招聘而非日期/倒计时。
- 去重以单位+岗位+批次+地点组合；仅明确批次/地点时自动合并。同组合证据冲突不择一，进review-queue.json。缺批次/地点不跨来源自动合并。
- 失败逐条写import-errors.json；不覆盖原材料。重复原始输入保留台账、source_refs和报告。

输入模板为fixtures/input.json，含明显虚构标识；复制格式时必须删除虚构内容并填写实际证据，不能把该样例导入真实目录。
