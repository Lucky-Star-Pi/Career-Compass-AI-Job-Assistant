# 求职助手应用

在本目录运行npm run build / npm start，应用监听3000端口。实际部署说明见../docs/OPS.md。
岗位数据为../data/processed/jobs.json的只读副本；更新后需要同步副本并重新build。

服务端变量：DEEPSEEK_API_KEY、PROFILE_COOKIE_SECRET，以及可选USER_DATA_DIR。可选DASHSCOPE_API_KEY启用qwen-plus备份；DeepSeek15秒→Qwen10秒→规则模板，每条响应携带mode。没有模型Key直接规则核对，不伪造调用。未配置稳定签名密钥时会话在进程重启后失效。
用户数据目录默认/opt/career-data；本地开发请把USER_DATA_DIR设为../data/private/local-users或其他app目录外路径。users.json仅保存scrypt盐与哈希；账号画像、简历原文和最近20条消息按userId隔离，文件原子替换与进程内写锁，不支持多进程同时写同一目录。

公开demo/demo2026为多人共享体验账号。聊天历史会持久化到账号文件，原始简历只进入独立resume字段，消息与cc.chat.v1离线缓存只留提交提示；可在顶部“修改”中删除。缓存绑定userId，服务端始终为准。传模型前仅作基础个人信息过滤，不保证识别所有个人信息，请只粘贴脱敏求职要点。
未确认画像也可提出槽位建议，普通聊天须点击确认；简历明确槽位自动填写并提供修改/清空。模型不得输出status；三态只由match.ts计算。模型日50次保护仅单进程有效，重启会重置，不替代持久预算监控。

验证入口：npm test、npm run build、python scripts/check_accounts.py；最终构建的隔离实例还可执行python scripts/check_xiaozhi.py。check_slots.py --live为第四轮真实模型验收脚本，仅使用合成资料，调用策略现已改为三级兜底。旧smoke.py/check_chat.py为此前未登录阶段的历史验收脚本，不作为当前账号流程入口。
单测使用本机Node24的内置TypeScript剥离；服务器Node20运行Next构建产物。第七轮仅新增pdfjs-dist@5.6.205，要求Node20.19+（或22.13+/24）；PDF模块仅在浏览器动态加载，主线程legacy handler不启动Worker。

第六轮：根页面公开SSR显示10条列表，前端筛选与排序；右下角面板承载原有对话/槽位/简历操作。收起时保持组件挂载，未登录只展示登录入口，不显示个人判定。登录但条件未确认时提示先确认；推荐B仅展示已载明条件的通过情况，源缺失和画像未足分开展示，match.ts保持不变。

PDF：≤5MB，最多前5页/6000字；文件不上传，文字提取失败或不足50字提示粘贴。只发送文字至既有私有简历通道；无OCR。不再提示偏好保存到账号文件preferences。推荐不等于报名资格通过。
