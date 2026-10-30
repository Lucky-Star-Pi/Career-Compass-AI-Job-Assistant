# B05-G 离线人工录入通道

状态：代码与模板可用，真实人工数据验收未完成。参赛者选择“先生成模板，稍后人工填写”。本轮没有请求职点迷津或公告站，没有调整采集器，没有读取会话文件，没有写processed。

## 实测

- python scripts/make_shortlist.py：总数22、优先0、备选3、不看19、无效输入0，exit=1。窗口2026-09-15至2026-10-30；真实候选不足以满足优先≥3，不提升备选。
- python scripts/manual_intake.py --check-only：0行；通过0、拒绝0、A档0，exit=0；这仅表示尚无输入，不表示15条或首条真实行通过。
- python scripts/manual_intake.py --input data/raw/MANUAL_TEMPLATE.csv --check-only：第2行拒绝“示例行必须删除”，exit=1。
- python scripts/test_manual_intake.py：9项通过，包括八硬字段、日期状态、URL、PII、UTF-8、引用逐字、文件复用、SAMPLE/空行、来源双引用保留及候选排序。测试仅在忽略的临时根目录使用合成输入，不计真实岗位。

## 产出与人工入口

- raw/SHORTLIST.csv：本地页级JSONL候选去重排序；collect-index仅作为历史索引，不据空索引推造岗位。
- raw/MANUAL_TEMPLATE.csv：固定28列，只有1条显式SAMPLE。
- raw/MANUAL.csv：空的28列表头工作表，未覆盖任何已有人工内容。
- MANUAL_GUIDE.md：逐列口径、三条铁律、Excel UTF-8、证据四行头部。
- scripts/manual_intake.py：check-only只读；普通模式仅raw导出。任一拒绝时记录输出空数组，报告保留全部逐行结果，不能导入拒绝行。
- 公告缺失策略按参赛者明确确认：只保留真实详情source_ref并标announcement_url缺失；有公告时保留两条实际引用，导入器不再覆盖第二条。

## 未满足项

优先档≥3未满足；首条真实行未提供，无法执行其通过验收；15条真实录入、人工确认及生产导入均未完成。不能用示例或原候选直接冒充人工核验结果。
真实人工岗位N=0、人工来源时间窗unknown、人工核验尚未开始。候选时间窗仅是旧材料的获取/发布日期，不代表人工真实性确认。

候选材料实际获取时间窗2026-10-30T20:46:47+08:00至2026-10-30T20:55:13+08:00，候选公告日期范围2026-07-26至2026-10-29。B05-G阶段没有实际导入；后续B05-H的人工URL请求属于另行授权，不能回填为G的网络行为。
