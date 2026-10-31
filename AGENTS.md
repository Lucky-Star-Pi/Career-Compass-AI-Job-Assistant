# 执行约定

- 第七轮覆盖旧的无PDF/无新依赖限制：仅新增pdfjs-dist，浏览器legacy构建同线程解析≤5MB/前5页/≤6000字，不上传文件；提取文字按账号私存，自动填写枚举画像并显式提供修改/清空。不改match.ts。小职气泡偏好按账号存储，DeepSeek15s→可选Qwen10s→规则；推荐仅声明已载明条件符合，未载明项逐条列出，不承诺报名资格。build/test通过后按本轮授权提交push并等待90秒核验。

- 第六轮覆盖第四轮页面布局与根页面登录门禁：公开SSR岗位列表优先，AI以右下角悬浮面板提供；只在助手内要求登录。保留既有账号存储、槽位确认和私有简历逻辑，不改match.ts、不新增依赖。本轮单提交feat: job list first with floating assistant，push后等90秒以HTTP核验公开首页。

- 第四轮A/B/C追加授权覆盖此前阶段限制：允许账号及用户隔离、对话优先界面、枚举槽位确认和私有简历文本；不改match.ts，不新增npm依赖。用户数据仅在应用目录之外USER_DATA_DIR（默认/opt/career-data），不得进入Git/日志。A、B、C分别提交推送后等待90秒核验，不手工改服务器应用文件。公开demo为共享体验账号，真实密码和简历不写仓库；固定体验凭据按用户要求公开展示。

- 当前夜间A→D授权覆盖此前阶段限制：修复数据后允许导入10条；整理文档；建立Next.js 15/React/Tailwind与已批准的react-dom、TypeScript、@types配套骨架。禁止部署、交互push与额外业务依赖；完成即停。主文档在docs/，历史报告在docs/reports/；证据路径保持data/raw不动。

- 冻结：Next.js 15 App Router / TypeScript / Tailwind；Neon PostgreSQL；DeepSeek-V4.1-Flash-1017 主（API ID：deepseek-flash），DashScope qwen-plus 备、qwen-turbo 轻任务；Vercel Hobby + Git。主模型变更依据参赛者2026-10-30追加指令，不再使用deepseek-chat。
- 不用向量库、微服务、多代理编排、OCR。本阶段不初始化框架、不安装依赖、不写业务应用。脚本仅 Python 标准库。
- 数据权限依据参赛者 2026-10-30 书面授权；B05-C单次≤150详情、最多4个jobs分片、匿名串行≥1.5s。B05-E追加允许登录后访问（仅本人账号、仅岗位详情、仅参赛演示），授权来自参赛者而非站点；先同页匿名/带Cookie最多2请求比较，未证实增益不得登录批量。禁/api/、验证码绕过、并发、全站抓取及列表翻页，遇条款冲突立即报告。
- B05-E凭据仅从data/private/session.json只读，禁止命令行传入、输出、日志或Git留存；台账只能记auth_mode及cookie哈希前8位。比较间隔≥2s；401/403/302或验证码/风控立即exit 4、不重试、不跟随跳转。不请求account/profile/resume/messages/applications或任何用户ID路径，不触发投递。登录数据不可称匿名公开数据。
- 采集UA联系地址仅从本地CAREER_COMPASS_CONTACT读取，按参赛者追加确认仅用于HTTP请求；控制台及run台账UA中的邮箱脱敏，不进仓库或协作记录。B05-C先修解析、以10页验证，通过后可150页或50条合格即停；不导入processed。基准2026-10-30，截止≥2026-10-31才open，优选≥2026-11-07，报名开始恒unknown；采集合格不代表个人资格eligible。
- 公开仓库仅可含结构化岗位数据及脱敏证据片段，不含整页 HTML 或个人联系方式。未知不等于不限，冲突入人工复核队列。
- eligible 仅用于用户画像已确认、所有硬条件有证据通过；关键未知或冲突保持 unknown；任一明确不符为 ineligible。
- 密钥、真实简历、手机号、邮箱、身份证、住址不进入仓库、日志、协作记录或模型提示词日志。原生记录本地隔离，先审查后交付。
- 每卡有意义提交，按实际时间记录；原文与 notes 分离；索引包含文件、时间、任务、SHA、哈希、export_method。
- 不修改代理、hosts、防火墙；首次 push 必须人工在场 GCM 授权，不索取凭据。费用操作先问人工。
- B05-G当前阶段仅离线候选清单、人工模板与证据校验；停止调整采集器，不请求职点迷津或公告站，不读取会话文件。只向raw导出，人工另行确认前不得导入processed；不得为凑优先数或15条而编造、升档。
- B05-H追加授权仅本人MANUAL_URLS.txt规范化后的详情清单，最多30条，串行≥1.5s、匿名无Cookie；不请求列表/API/sitemap/公告站，不发现新URL。仅H阶段覆盖G纯离线约束。任何列PENDING未补必须拒绝合并，人工确认前不写processed。
- B05-I仅离线重解析既存证据，零网络；旧表及台账保留.v1，证据不变。显式长期招聘可open，但截止unknown且open_basis=长期招聘，不伪造日期、不等于个人eligible；公告未写明仍unknown。备注可空，其他PENDING与证据校验仍严格。
