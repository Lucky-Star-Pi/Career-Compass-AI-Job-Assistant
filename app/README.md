# 本地应用骨架

在本目录运行npm run build / npm start，在3000端口启动，本机通过http://127.0.0.1:3000访问。没有部署步骤或公网承诺。
数据为../data/processed/jobs.json的只读副本；更新源数据后须重新复制并build。
可选服务端环境变量DEEPSEEK_API_KEY、PROFILE_COOKIE_SECRET（不要提交真实值）。没有模型Key返回“未接通”桩，不伪造调用。签名密钥未配置时仅用本进程随机密钥，重启使条件失效；多实例部署前必须配置稳定密钥。
问答只传本页候选和条件，不保存聊天，不记录提示词、Cookie或密钥。未确认画像不调用模型。日50次保护仅在单进程内生效，重启会重置；本阶段未做持久预算或账户额度实测。
规则是保守的最小实现：未核验来源/专业目录歧义/未支持的附加条件一律unknown。原始10条并未被标成eligible。合成规则测试不计真实岗位。

验证：npm test（9项规则测试）、python scripts/smoke.py（仅本机生产接口，移除模型Key）、npm run build。Next15不兼容TypeScript7，本次使用TypeScript5并提交锁文件。规则函数不读取时钟，调用端显式传入上海日期；关键限制未写明仍unknown。
