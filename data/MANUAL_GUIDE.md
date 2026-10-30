# B05-G 人工录入指南（离线，目标15条）

本轮停止调整采集器，不请求职点迷津或公告站。候选池仅来自已有page-records.jsonl；SHORTLIST.csv是线索，不是已核验或可报名清单。近45天明确按2026-09-15至2026-10-30（含边界）判断，单位缺失的校招只能备选；不足3条优先如实说明。

## 三条铁律

1. **unknown≠不限**：缺失、无法确认填unknown，不能自动填不限；原文明确不限时才可录入该原句。
2. **条件原文逐字命中**：保持原文和换行，不拼造连接词；条件原文与证据引用都必须在同岗TXT中逐字找到。结构校验通过不等于个人资格eligible。
3. **一岗一文件**：每岗独立UTF-8 TXT，编号唯一，文件不能复用（含软/硬链接）。不要把整页HTML、个人联系方式、简历或凭据保存进去。

## 操作顺序

1. 查看data/raw/SHORTLIST.csv；缺口不靠升档凑数。
2. data/raw/MANUAL_TEMPLATE.csv含一行SAMPLE，必须删除示例。data/raw/MANUAL.csv已创建为只有表头的空工作表；再次生成模板不会覆盖本人已填写的文件。
3. 本人使用已合法取得的材料填写15岗，每岗另建证据TXT。本coding agent本轮不访问来源网站、不代填来源事实。
4. Excel请选择“CSV UTF-8（逗号分隔）”，保留28列原顺序；证据路径、URL及编号列按文本处理。条件原文/引用包含逗号或换行时让Excel正常引用，不手工拆行。
5. `python scripts/manual_intake.py --check-only`：只读校验，不写任何输出。空输入打印0行，不代表15条验收通过。
6. 校验无拒绝后`python scripts/manual_intake.py`仅生成raw/MANUAL.records.json及MANUAL_REPORT.md；如任一行拒绝或表头错误，记录输出为空数组，防止使用旧导出；原CSV和TXT不改动。报告仍逐行列通过与拒绝。
7. 只有人工另行确认后才执行`python scripts/import_data.py --input data/raw/MANUAL.records.json`，再运行生产闸门；本轮禁止执行该实际导入。

## 固定28列

| 列 | 填写口径 | 校验/缺失处理 |
|---|---|---|
| 编号 | 如M01，本人定义的岗位编号 | 硬性；唯一，防重按大小写不敏感；SAMPLE不能导入 |
| 岗位名称 | 来源原岗位名 | 硬性，不得unknown |
| 单位名称 | 可确认的真实单位名称 | 硬性，不凭标题地区猜单位 |
| 单位性质 | 央企/国企/事业单位/民企/unknown | 只接受这五个枚举；不根据名称自动认定 |
| 招聘类型 | 原文校招/社招等 | 缺失unknown，不凭岗位名推定 |
| 批次届别 | 原文批次或届别 | 缺失unknown，不从发布日期推断 |
| 工作地点 | 原文地区 | 缺失unknown，不写个人住址 |
| 详情页URL | 职点迷津详情来源 | 硬性，http(s)，主机仅zhidianmijin.com.cn或www版本；无fragment、内嵌凭据及受禁参数 |
| 公告URL | 实际公告来源 | 可unknown；有值须https且非职点迷津及其子域，不能伪造公告引用 |
| 报名入口URL | 正常报名链接，仅保存不请求 | 可unknown；有值须https且无凭据/受禁参数/fragment |
| 发布时间 | 原文日期 | YYYY-MM-DD或YYYY年M月D日，缺失unknown；不能用lastmod替代 |
| 报名开始 | 原文明确的开始日期 | 同上，可unknown，禁止从发布时间推算 |
| 报名截止 | 原文明确的截止日期 | 同上，可unknown；不补23:59 |
| 学历 | 原文学历要求 | 可unknown；有值须在TXT逐字出现 |
| 学位 | 原文学位要求 | 同上，不从学历推算 |
| 专业 | 原文专业名称/代码/范围 | 同上，不把相近专业自动视为通过 |
| 毕业时间 | 原文毕业时间/届别区间 | 保留原文，不强制改成单一日期；有值须在TXT出现 |
| 工作经验 | 原文年限/应届要求 | 可unknown；不根据岗位名推定 |
| 政治面貌 | 原文要求 | 可unknown；只录岗位条件，不录个人信息 |
| 证书 | 原文证书限制 | 可unknown |
| 年龄 | 原文年龄及计算基准 | 可unknown，不自行计算基准日 |
| 其他限制 | 公告通用要求及例外原文 | 可unknown，不遗漏备注限制 |
| 条件原文 | 连续证据段，可带原有换行 | 硬性；必须在TXT逐字出现，不trim改写 |
| 证据引用 | 原句或原文片段 | 硬性；必须在TXT逐字出现 |
| 开放状态 | open/closed/unknown | open须截止≥2026-10-31；closed须截止<2026-10-30；本任务口径下2026-10-30只能unknown；unknown不自动升级 |
| 采集时间 | 本人实际获取该材料的时刻 | 硬性；ISO8601显式+08:00，不回填推测时间 |
| 证据文件 | 相对仓库路径，如data/raw/manual/M01.txt | 硬性；路径必须在data/raw内，UTF-8 TXT，不能指向private或fixtures |
| 备注 | 缺口、来源方式与人工核验说明 | 可unknown；有“示例”即拒绝；不写账号、Cookie或个人信息 |

受禁查询参数名（大小写不敏感，URL解码后）：token/access_token/key/api_key/apikey/secret/session/auth/sign/signature/password/pwd/ticket。所有单元格和证据均扫描邮箱、11位手机号及证件号；检测到时仅报行号/类别，不打印原文。正则不能替代完整人工隐私复核。

## 证据TXT四行头部

以下为格式占位说明，不是可导入真实数据；替换成该岗CSV一致的真实值：

```text
# 岗位名称：与CSV岗位名称完全一致
# 详情页URL：与CSV详情页URL完全一致
# 公告URL：实际公告URL，未提供则unknown
# 采集时间：与CSV采集时间完全一致
此后仅放获准保存、已脱敏的真实证据正文；不要把本说明复制进证据。
```

日期列只解析发布时间、报名开始、报名截止；采集时间单独按完整ISO时间校验。学历等条件字段保留原文，normalized=unknown，逻辑未解析不会擅自标AND或资格通过。

## 来源与输出边界

参赛者本轮明确确认：缺公告时允许只保留真实详情引用并标缺失；不生成假的第二条source_ref。公告有值时source_refs保留详情与公告两条，二者均关联同岗证据TXT及其实际SHA256。导入器已保留这些引用，不会丢掉公告来源。

输出固定status=unknown、profile_confirmed=false、is_fixture=false；human_verification=pending，表示结构/证据校验不等于独立来源核验或学生资格确认。所有合并与生产导入须人工另行确认。

## B05-H URL清单追加通道

H按本人清单另行授权抓详情，边界及命令见MANUAL_URL_GUIDE.md，不再抓列表或API。`--auto`接受固定10列FILL_ME，以编号覆盖28列auto。任何PENDING残留均拒绝；原PENDING留空仍保留PENDING。check-only不改证据、不写raw或processed。采集证据保留BATCH前三行并增加公告URL行，只有--auto合并模式额外接受该四行头。
