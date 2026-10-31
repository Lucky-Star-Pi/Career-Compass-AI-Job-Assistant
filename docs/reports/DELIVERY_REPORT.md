# 提交包交付核验

本轮只修改Markdown说明与目录位置；离线评测在独立提交36a3f69中完成。最后业务变更e122c2c已推送，公开首页HTTP200且页面脚本含scrollIntoView与preventScroll；未读取服务器Git HEAD，不把行为验证冒充精确服务器提交证明。本轮不打tag，v1.0-submit由参赛者最终确认后创建。

## 目录与材料

- README按十节组织，入口/账号前置、可信机制逐条有代码/测试/数据依据，第7节引用真实8例指标，第8节列10条限制。
- docs根目录仅保留SUBMISSION、OPS、DECISIONS、DATA_SCOPE、PLAN、STAGE1_REPORT和reports目录；两份阶段清单归档到reports/archive。根目录仅保留规定五个文件，原考题PDF本地保留并由Git忽略。
- 20个历史文档或批次元数据归档，映射及哈希见[ARCHIVE_MAP.md](ARCHIVE_MAP.md)。正式脚本仍引用的pages/证据TXT/自动表/FILL_ME/collect-index保留原位；两份岗位JSON和36份evidence.txt路径及字节未改。
- 删除12个临时log/tmp/pid/probe产物，不触碰data/private、native原件、node_modules、.next或正式scripts。合成UI截图作为文档附件保留，含义见[编辑区验收](EDITOR_SCROLL_REPORT.md)。

## 真实离线检查

- node --experimental-strip-types eval/run_eval.ts：一致8/8（100%）；已判定3/3（100%）；unknown5/8（62.5%），仅规则层、4个不同岗位、无eligible正例。
- python scripts/validate_data.py：PASS: production records=10。
- python scripts/test_data_pipeline.py：PASS all offline pipeline regression checks。
- 38项npm单测及中文路径build此前在e122c2c交互修复时均通过；本轮不修改业务代码，不冒充重新完成部署构建。

## 文件与隐私检查口径

参赛者指定的宽泛文件名过滤会命中合法源码app/lib/session.ts、Next类型声明app/next-env.d.ts、正式脚本scripts/save_session.py及归档环境清单。它不能等同于凭据泄露检查；不删除或改名这些正式文件来制造空输出。应另确认没有.env.local、data/private/、node_modules/、.next/、实际session.json、原生记录原件被Git追踪。最后实际命令输出在本节后追加。

## 发布健康与版本边界

本报告在最终push前形成；发布后等待至少90秒，再核对健康接口。无服务器SSH会话时只能从公开HTTP核验服务，本机127.0.0.1检查会明确标注本机，不冒充服务器内部自查。模型及用户私有接口不参与本次整理检查，7天保活仍由参赛者按[OPS](../OPS.md)执行。

## 暂存清单的实际命令输出

```text
git ls-files | wc -l
208
宽泛env/session/private/node_modules/.next路径过滤：
app/lib/session.ts
app/next-env.d.ts
docs/reports/archive/ENV_CHECKLIST.md
scripts/save_session.py
README/SUBMISSION占位词检查：no placeholders
grep -c unknown README.md：4
node -e "1"：sanity ok
精确敏感/忽略产物路径命中：0
README本地链接：84，失效或大小写不一致：0
```

根目录五个文件与docs根目录七项均符合整理清单；未改业务、规则或正式脚本。历史批次仅移动元数据，仍受正式脚本引用的证据路径保留，映射表按Git字节复核。仓库不含实际.env.local、session.json、私有用户目录或原生记录原件。此处文件名检查不等同于对Git全历史的完整密钥扫描。

TIMELOG记录区间去重后为4.5–4.8小时，精确计算下界/上界为4.5478/4.7894小时；仅记录墙钟范围，不代表精确净投入。本轮记录截至2026-10-31T15:36:38+08:00，其后提交与等待见工具输出。
