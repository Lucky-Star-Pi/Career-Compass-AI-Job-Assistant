# 打开画像编辑区的滚动与焦点验收

提交：`fix: scroll to profile editor when opening it`，SHA由本提交Git历史定位。本文件于push前记录；push后等待至少90秒，以后续公网HTTP与新页面脚本检查为准。

- JobAssistant.tsx新增editRef与openEditor(updates?)，两处修改入口复用。60ms后平滑滚到编辑区；350ms后聚焦第一个select，使用preventScroll:true。顶部使用已保存profile；消息入口将该条白名单updates合并进草稿并取消确认标记。不再以重复点击关闭编辑器。
- npm test --prefix app：38/38通过；npm run build --prefix app：中文路径exit=0。
- 本机生产构建3120使用应用目录外的隔离合成账号。20条合成消息初始scrollTop=8000、scrollHeight=8343、clientHeight=343；两家模型Key都禁用，未调用模型或读取真实简历。
- 顶部入口：学历=本科，focused=true，scrollTop=196.8；下拉顶部127.4、容器顶部89.6，编辑区进入视野。
- 消息入口：学历=硕士，focused=true；专业=会计学、年份=2028、城市=上海市、CET-6=true。scrollTop同为196.8，聚焦后保持编辑区位置，无第二次滚动偏移。
- 截图只含合成条件，在本地忽略目录data/.tmp/editor-scroll.jpg，不进入公开仓库；浏览器临时标签和测试进程会在收尾关闭。
- 业务源代码仅修改JobAssistant.tsx；无新依赖，规则/模型/数据/账号接口未改。此记录为verification-note，非原始协作导出，native原件未读取或变更。
