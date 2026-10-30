# 技术选型冻结单

状态：参赛者 2026-10-30 开工指令 A2 已冻结；不再次选型。冻结不等于账户、构建或模型可用性已验证。

变更记录（2026-10-30）：参赛者明确指定使用最新DeepSeek-V4.1-Flash-1017。官方当日模型表确认其调用ID为`deepseek-flash`，Base URL为`https://api.deepseek.com`。这是人工批准的冻结单变更，取代原deepseek-chat主模型；Qwen备选不变。该ID是服务别名，不能承诺未来始终锁定1017版本；上线时记录实际返回的模型标识。

| 范围 | 冻结选择及理由 | 放弃的候选及原因 | 24h 风险 | 费用与降级 |
|---|---|---|---|---|
| 前端/API | Next.js 15 App Router + TypeScript + Tailwind，单仓库便于同部署 | React+FastAPI 增加部署与联调面 | 中文路径构建、版本安全补丁需后续核验，不锁过期补丁 | 不安装依赖；后续选 15 系列经安全核验补丁，基础页面降级 |
| 数据库 | Neon 免费 PostgreSQL；@neondatabase/serverless；首版手写 SQL 迁移 | Supabase 增加账户；本地 SQLite 不适合无持久盘部署 | 免费额度、连接及休眠未验证 | 基础设施0元；超额不升级，缩减数据/停写并披露 |
| 主模型 | DeepSeek-V4.1-Flash-1017，API ID deepseek-flash，按用户追加指令 | deepseek-chat已退役；OpenAI不增加账户和预算 | 账户余额及真实调用未验证；别名版本可能更新；JSON输出仍需契约校验 | 沿用≤100元模型预算；失败按既定Qwen备选降级，不自动调用付费搜索 |
| 备选/轻任务 | DashScope compatible-mode qwen-plus / qwen-turbo | 多供应商路由编排超范围 | 账户额度、结构化输出和地区需实测 | 模型总额≤100元；超时回退表单规则，未确认额度不发请求 |
| 简历 | 服务端文本抽取，扫描件粘贴文本 | OCR耗时且可能出错 | PDF库及格式待下一阶段测试 | 无付费解析服务；失败明确回退 |
| 部署/CI | Vercel Hobby + Git 自动部署 | 自建服务器增加成本维护；Cloudflare Pages 仅备选 | 大陆访问、免费条款和限额待核验；Pages不能直接等价承载全部Next动态API | 0元，备选切换需先验证动态运行时，不假定兼容 |
| 日志 | JSON + requestId，Vercel日志 | 独立日志平台增加配置 | 保留期限、敏感内容泄漏 | 只记录类别/耗时/版本，禁正文及凭据 |
| 协作记录 | native原样本地复制主通道，人工网页原文补通道 | 事后总结不能替代原始记录 | 完整原件不适合直接公开 | 本地审查隔离，缺失如实披露 |

不用向量库、微服务、多代理编排、OCR；本阶段不初始化应用框架或安装业务依赖。

## 官方价格核查（2026-10-30，Asia/Shanghai）

单位：人民币/百万 tokens；公开价不是账户余额证明，未进行计费调用。

- [DeepSeek官方退役公告](https://api-docs.deepseek.com/news/news260424/)：deepseek-chat / deepseek-reasoner 于 2026-07-24 15:59 UTC 后不可访问。因此 deepseek-chat 当前单价记“不适用（已退役）”，不引用历史价格冒充当日价格。
- [DeepSeek当日价格页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)（追加指令后再次核对）：deepseek-flash对应DeepSeek-V4.1-Flash-1017；空闲/高峰：缓存命中0.02/0.04、未命中1/2、输出4/8。现作为主模型预算依据；账户余额、实际调用仍未验证。
- [Qwen价格页](https://help.aliyun.com/zh/model-studio/model-pricing)：北京区 qwen-plus，输入≤128K：输入0.8、非思考输出2、思考输出8；128K–256K：2.4/20/24；256K–1M：4.8/48/64。首版限制在第一档、非思考模式。
- [qwen-turbo官方模型页](https://help.aliyun.com/en/model-studio/qwen-turbo)：北京区输入0.3、非思考输出0.6、思考输出3。地区和账户优惠仍由人工控制台核对。

预算：总额50–150元；基础设施0元；模型≤100元，留50元机动。建议模型累计50/80元告警、100元停用；告警配置未验证，不声称已生效。任何充值、升级和付费资源先问人工。
