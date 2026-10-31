# 第七轮：小职验收记录

本轮功能提交：`feat: xiaozhi assistant with pdf resume and tiered fallback`，SHA由本提交的Git历史定位。本文件在push前形成；发布后至少等待90秒，以随后公开HTTP实测为准，不能把本地成功当作已上线。

## 改动与边界

- 唯一新增直接依赖：pdfjs-dist@5.6.205（legacy API与worker handler在浏览器主线程载入，不创建Worker）。依据为[PDF.js官方源码说明](https://mozilla.github.io/pdf.js/api/draft/api.js.html)中`globalThis.pdfjsWorker.WorkerMessageHandler`的同线程处理路径；不使用已失效的disableWorker选项。
- PDF输入仅本机解析，不上传文件。上限5MB、前5页、6000字；不足50个非空白字符或解析失败提示粘贴；不做OCR。只把提取文字送入既有账号私有resume字段，GET画像接口不返回原文，消息与离线副本只保存提交提示。
- 简历提取明确枚举槽位后自动填写画像，顶端标示来源并提供修改/清空；模型均失败时仅从明确且无歧义的枚举文字提取。换一份简历时不沿用旧字段；没有可提取槽位则清空旧画像。普通对话的建议仍需确认。
- 小职球为“职”，空态三行介绍及三个快捷按钮；第三个按钮必须先选过岗位。气泡不按时间消失；知道啦只关闭本次，不再提示持久化到登录账号preferences，匿名用户先登录后保存。
- DeepSeek 15秒→可选Qwen qwen-plus 10秒→规则。每层一次请求，JSON截断、来源/隐私/推荐口径校验失败均进入下一层；Qwen未配置直接跳过。mode随每条回答保存，UI展示生成来源；规则模板不伪称真实模型调用。
- 推荐B在独立recommendation.ts中解释既有checks：有明确不符则指出字段；已载明但用户未提供或规则尚不能解释的条件不通过；只有已载明项均通过、来源已核对且开放时才展示条件符合，原文缺失字段逐条列出。核心unknown仍保持unknown，源缺失从不算pass。match.ts与10条岗位JSON均无改动。

## 真实命令结果

| 命令 | 结果 |
|---|---|
| node app/node_modules/typescript/bin/tsc --noEmit --project app/tsconfig.json | exit=0 |
| npm run build --prefix app | 中文路径exit=0；Next 15.5.28；根页First Load JS 118kB，PDF另行动态载入 |
| npm test --prefix app | tests=35, pass=35, fail=0 |
| python scripts/validate_data.py | PASS: production records=10 |
| python scripts/test_data_pipeline.py | PASS all offline pipeline regression checks |
| python app/scripts/check_accounts.py | 公共SSR10卡/私有API401、demo登录、双账号隔离、独立Cookie会话恢复、重启持久化、退出全部PASS |
| python app/scripts/check_xiaozhi.py | 账号偏好隔离/401/非法键拒绝；错误DeepSeek Key转rules、3条成对来源；简历自动填写/原文不回显；新简历无槽位清旧画像；删除与清空全部PASS |

check_xiaozhi针对本机3117最终生产构建，独立USER_DATA_DIR在应用目录之外；DeepSeek故意使用无效测试值，Qwen置空，不读取或修改真实模型Key。合成测试账号、PDF及运行文件在Git忽略目录data/private与data/.tmp，未触及线上账号、未记录真实简历或凭据。

## 浏览器实际观察

1. 公开首页SSR显示10条；未登录面板为体验账号入口；登录后显示小职三行介绍和按钮。
2. 选择带文字的合成中文PDF后显示“已根据简历填写”：本科、国际商务类、2027届、湛江市、CET-4与C1驾驶证。顶部有修改/清空，01卡展示5项已载明通过与7项公告未载明；03/05明确学历不符。回复标签为规则核对结果，原文未进入消息。
3. 图像式PDF显示“这份 PDF 没读到文字，可能是扫描件，请改为粘贴文本”；超5MB显示大小限制，页面继续可用。
4. 知道啦后气泡消失，刷新再出现；不再提示后刷新不出现。最终构建复验：打开面板后再登录/收起，气泡不会被偏好读取重新弹出。
5. UI截图只含合成测试信息，保存在本地忽略目录data/.tmp/r7-xiaozhi.jpg；不是生产用户资料，也不代替原始协作记录。

## 证明范围与剩余限制

- Qwen成功切换使用模拟HTTP响应进行单测；本轮没有Qwen真实调用或额度验证，不声称其账户已配置。DeepSeek错误Key的真实HTTP流程已验证规则兜底，不更改线上密钥做故障演练。
- PDF为同线程提取，大文件可能短时占用UI；扫描件不识别，复杂多栏/字体或加密文件可能失败。前5页/6000字为明确截断边界，不宣称完整解析任意简历；自动提取仍需用户看摘要并修改。
- 仍是HTTP入口、10条样本、单进程文件写锁；demo由多人共享，切勿提交真实简历。源公告可能变化，符合已载明项不等于获得报名资格。
- pdfjs-dist引擎要求Node20.19+/22.13+/24；本机Node24通过，服务器Node20的小版本未由本轮工具读取。不擅自升级服务器或配置备份Key。
- 规则核心、来源证据与native原件均未改；当前记录是verification-note，不是会话原始导出，后续原始协作记录交付缺口仍需按DELIVERY_PLAN披露。
