# 部署与运维

## 1. 实际架构

腾讯云 ECS，TencentOS 4、2C4G，Node 20 + pm2 + cron，Next.js 应用监听3000端口。入口为 http://118.89.79.239:3000，列表免登录，助手需登录。以上环境及线上健康检查结果来自参赛者2026-10-31状态同步；早期Vercel/Neon选型记录不代表当前实际部署，当前数据为只读JSON。

## 2. 自动部署链路

push → GitHub → 服务器每分钟执行git fetch → 有变化则rsync到运行目录（保留.env.local）→ npm ci && npm run build → pm2 restart career。参赛者已实测约80秒生效；这是cron轮询部署，未配置标准托管CI流水线。

应用与文档修改都从仓库提交、push，不手动改服务器文件。唯一配置例外是参赛者本人维护/opt/career/app/.env.local。push失败不会触发新版本；不要将本地提交直接标为线上版本。发布后等待至少90秒，核对站点、/api/health与本轮修改的实际页面文案，再登记对应推送SHA；服务端HEAD未直接读取时明确其证明范围。

## 3. 关键路径

| 用途 | 路径 |
|---|---|
| 应用运行目录 | /opt/career/app |
| Git仓库 | /opt/career/career-repo |
| 部署脚本 | /opt/career/deploy.sh |
| 部署日志 | /var/log/career-deploy.log |

当前发布记录见[提交说明](SUBMISSION.md)。服务器既有脚本由参赛者维护，本轮仅通过Git发布；没有连接服务器修改脚本或配置。

## 4. 七天保活安排

从实际提交日起至少7天不关机、不释放实例；按2026-10-31提交暂安排至2026-11-07，若提交时间顺延则保活截止同步顺延。参赛者负责确认pm2自启，每天打开一次站点，第3天、第6天各运行一次确认画像→查看条件与来源→AI问答→清除条件完整流程，并核对实例到期、账户余额与模型额度。

cron每分钟巡检仓库版本并触发部署，不等同于独立HTTP健康探针；站点健康仍按上述人工计划检查。参赛者给定按量计费估算约50元/周，并非已核对账单；实际费用以云控制台为准。本文件不购买、不升级实例。到期与余额的控制台证明未纳入本次工具实测，未来7天可用是运维承诺与安排，不能由一次访问证明。

## 5. 故障排查

参赛者在服务器依次检查：`pm2 logs career` → `curl 127.0.0.1:3000/api/health` → 云安全组是否放行3000端口。自动部署异常再检查/var/log/career-deploy.log及Git连接、npm ci和build结果；保持从Git修复，不临时覆盖服务器应用文件。

日志只记录状态和必要错误类型，不粘贴密钥、Cookie、用户输入、真实简历或个人联系方式。外部访问失败但本机健康时核查端口与实例状态；模型失败时检查额度和服务端配置，不把降级回复当真实调用成功。

## 6. 密钥与发布核验

/opt/career/app/.env.local保存DEEPSEEK_API_KEY和PROFILE_COOKIE_SECRET，可选DASHSCOPE_API_KEY启用Qwen备份，权限600，不进入Git或Docker构建上下文。配置由参赛者本人负责，本文不读取、展示或复制密钥；稳定Cookie签名密钥用于重启后的画像一致性。

参赛者已报告线上/api/health的data_count=10、persistent_cookie_secret=true，以及一次connected=true、约1.4秒的对话实测。该事实与本轮发布是否成功分开登记；本轮GitHub连接失败时继续使用先前线上版本，不能依据既有健康结果宣称新提交已上线。

第四轮账号存储：默认/opt/career-data（可用USER_DATA_DIR指定应用目录外路径），users.json仅保存scrypt盐和哈希，profiles/<userId>.json保存该账号画像、私有简历与最近20条消息。运行时自动建目录，文件模式600、目录700；单进程写锁与临时文件rename用于原子替换。该目录不在rsync应用路径内；不要把它拷入源码或部署日志。公开demo为共享体验账号。

第七轮：PDF仅浏览器动态载入pdfjs-dist legacy构建，在同一线程提取文字；不上传文件、不做OCR。pdfjs-dist@5.6.205的Node引擎声明为20.19+/22.13+/24，本机Node24构建通过；服务器Node20的具体小版本未在本轮读取，若npm提示EBADENGINE由参赛者核对版本，不擅自升级服务器。偏好与画像来源标记随账号文件原子保存，不放在应用目录。
