# 求职助手应用

在本目录运行npm run build / npm start，应用监听3000端口。实际部署说明见../docs/OPS.md。
岗位数据为../data/processed/jobs.json的只读副本；更新后需要同步副本并重新build。

服务端变量：DEEPSEEK_API_KEY、PROFILE_COOKIE_SECRET，以及可选USER_DATA_DIR。没有模型Key返回“未接通”，不伪造调用。未配置稳定签名密钥时会话在进程重启后失效。
用户数据目录默认/opt/career-data；本地开发请把USER_DATA_DIR设为../data/private/local-users或其他app目录外路径。users.json仅保存scrypt盐与哈希；账号画像、简历原文和最近20条消息按userId隔离，文件原子替换与进程内写锁，不支持多进程同时写同一目录。

公开demo/demo2026为多人共享体验账号。聊天历史会持久化到账号文件，原始简历只进入独立resume字段，消息与cc.chat.v1离线缓存只留提交提示；可在顶部“修改”中删除。缓存绑定userId，服务端始终为准。传模型前仅作基础个人信息过滤，不保证识别所有个人信息，请只粘贴脱敏求职要点。
未确认画像也可提出槽位建议，但必须点击确认才能写入画像和重新匹配。模型不得输出status；三态只由match.ts计算。模型日50次保护仅单进程有效，重启会重置，不替代持久预算监控。

验证入口：npm test、npm run build、python scripts/check_accounts.py。check_slots.py --live会执行最多3次真实模型请求（各最多重试一次），仅使用合成资料。旧smoke.py/check_chat.py为此前未登录阶段的历史验收脚本，不作为当前账号流程入口。
单测使用本机Node24的内置TypeScript剥离；服务器Node20运行Next构建产物。没有新增npm依赖。

第六轮：根页面公开SSR显示10条列表，前端筛选与排序；右下角面板承载原有对话/槽位/简历操作。收起时保持组件挂载，未登录只展示登录入口，不显示个人判定。登录但条件未确认时，三项徽章显示破折号而非虚构数值；确认后复用summarize显示实际计数。
