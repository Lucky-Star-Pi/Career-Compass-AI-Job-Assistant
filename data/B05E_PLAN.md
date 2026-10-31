# B05-E：仅本人会话的两请求差异验证

当前状态：已完成文档前置、比较代码和离线测试，尚未实际验证，不假定有增益或无增益。现有匿名batch_jobs.py未接入Cookie，未改变其筛选语义。

实际预检：已运行下方比较命令，输出`STOP: PrivateSessionMissingOrInvalid; no comparison requests sent`。当前指定私有文件未检测到，实际HTTP请求0次；未生成AUTH_NO_GAIN/AUTH_GAIN结论，也未进入第二阶段。本轮7项登录比较测试及10项原采集回归通过。B05-E改动暂留工作区，等待本人保存有效私有文件后再实际比较，并按结果选择用户指定提交标题。

## 本人操作

参赛者本人在浏览器F12 Network复制本人账号Cookie请求头的值，在本地data/private/session.json保存cookie和exported_at（ISO8601+08:00）；不要把Cookie发送到聊天、命令行、日志或Git。该目录已被gitignore排除。脚本只读文件，不续写、不修改、不把Set-Cookie保存回来。Cookie字段应只包含请求头值，不带“Cookie:”前缀。

命令：`python scripts/collect_jobs.py --compare-auth https://www.zhidianmijin.com.cn/jobs/012b1d2f-1b4b-2b49-6996-4c776b65d661`。
该URL为先前实际访问的AI数据工程研究岗；本次重访仅用于明确授权的匿名/登录差异比较，不算新增岗位采集，不改collect-index。
UA仍从本地CAREER_COMPASS_CONTACT取得，匿名和登录请求完全相同，不改指纹、IP或系统代理。

## 第一阶段规则

- 最多2个GET：同一详情匿名一次，完成后≥2s再带Cookie一次；本日robots已有实测，比较不额外发robots或sitemap请求。
- 严格限定www.zhidianmijin.com.cn的https /jobs/<uuid>，无query、fragment或用户路径；不跟随任何重定向，不读账号、简历、消息或申请，不触发投递动作。
- 401/403/302及其他重定向、429或验证码/安全验证等风控立即exit 4；传输/解析异常记inconclusive，不重试、不继续发请求凑2次。
- run.json只存两次HTTP状态、字段名集合、岗位目标文本长度、登录提示布尔值及差异；认证元数据仅auth_mode和cookie_sha256_8。没有Cookie值/名称、exported_at、响应头或正文。
- 对比的是可解析岗位字段，剔除时间戳、路径等自动元数据；正文更长本身不构成字段增益。
- 缺少会话、比较URL不在白名单或格式错误：发送0请求，不能生成无增益结论。
- 截止仍为公告未写明且无新增字段：AUTH_NO_GAIN.md明确“登录不增加数据，放弃登录态采集”；不改匿名批量逻辑。
- 有新增字段：AUTH_GAIN.md逐项列出字段名；之后才实现第二阶段，不把未经证明的会话当已登录成功。不能独立验证会话有效性时如实披露本比较仅反映本URL/该Cookie的响应。

## 第二阶段条件与披露（未执行）

本仓库未发现B05-D产物，以本次用户给定规则为唯一第二阶段口径：单位有值、明确校招、发布日期可解析、条件原文逐字命中、无PII；A档截止具体且≥2026-10-31，B档截止unknown，分档统计，B档禁止称为可报名。目标50，不足如实报数。
有字段增益后才接入本人会话，单次≤150页、间隔≥2s；只允许jobs/指定sitemap/robots，禁/api/及任何用户路径。不能扩大第一阶段的两请求授权来做无门禁批量。
实际使用后提交说明必须写：“采集使用了参赛者本人账号的登录态”。这是参赛者授权而非站点许可；不把登录取得的信息称作匿名公开数据。

## 提交分支

无增益实测后：docs: record that login adds no job fields。
仅在第二阶段实际执行后：feat: add opt-in session auth for job detail collection。
会话未提供或比较失败：只报告准备状态/阻塞，不伪造上述任一实测结论。
