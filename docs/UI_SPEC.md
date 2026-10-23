# 百草园 UI 实施规范

2026-10-22，已随本轮实现统一tokens/AppShell、发现卡片、关注时间线和独立页面；实际截图和未验证项见IMPLEMENTATION_REPORT。API 与业务规则见 API_CONTRACT.md，验收见 ACCEPTANCE_SCENARIOS.md。

## 设计变量

统一 CSS variables：--bg:#faf9f6，--surface:#fff，--text:#242424，--muted:#756f69，--border:#e9e5df，--accent:#c94440，--accent-hover:#b43733，--success:#27805d，--warning:#a3630c，--danger:#b93e3e。主色用于发布、选中导航与关键操作，主色与白色文字对比度4.79:1，与暖白背景4.55:1；正文和辅助文本另用深灰色。字体 system-ui/PingFang SC/Microsoft YaHei；body16px/1.65，meta13px/1.5，标题24px/1.35，卡片标题16px/1.5。间距4/8/12/16/24/32；卡片圆角12、控件10、胶囊999；阴影仅用于浮层；z-index：导航20、遮罩50、详情60、查看器70、Toast100。过渡180ms，prefers-reduced-motion 关闭非必要动画。focus-visible 为3px清晰轮廓，不能仅靠颜色表达状态。

## 页面和组件边界

AppShell 负责导航、顶搜、账号入口与 main landmark，不保存帖子副本。页面负责 query、请求、loading/error/分页与取消；业务 composable 以稳定 ID 更新实体与服务端权威计数。展示组件只接收 props 并发出动作；同一互动入口共用 pending key（entity+action），失败保留原状态。禁止在卡片内部另建 API 数据状态。

基础组件：BaseButton/IconButton（loading+disabled+aria-label）、Avatar（URL失败→昵称首字，无空图）、FormField（label/错误关联）、Tag、Skeleton、EmptyState、ErrorState（真实重试）、ConfirmDialog、Toast。弹窗优先原生 dialog 或经测试的 Element Plus 对话框，不重复引入组件体系。后台保留 Element Plus 独立导航。

AppShell：桌面≥1280 固定224px侧栏，品牌图形用简洁叶形SVG+百草园字标；发现/关注/通知/收藏/主页/设置，发布主按钮，底部账号。768–1279收72px图标栏，aria-label和可见 tooltip；<768取消侧栏，顶搜和标题，底栏发现/关注/发布/通知/我的，安全区 env(safe-area-inset-bottom)。所有入口有实际路由或明确登录提示，无假统计。

## 路由和真实数据

| 路由 | 页面职责与数据 | 页面特殊状态 |
| --- | --- | --- |
| /?nav=推荐/热门/更新 | FeedPage，search/recommend 分页摘要 | 空库明确邀请发布，不自动造数据；推荐规则回退无训练成功文案 |
| /following | FollowingPage，关注作者动态单列 | 未登录保留来源登录；空关注有发现入口 |
| /search?q=&type=posts&tag= | SearchPage，帖子/用户独立请求 | query是状态源；取消旧请求；无结果保留词并能清空 |
| /detail/:id | DetailPage，GET实体+评论分页 | 404统一“内容不可用”；作者管理另入口看原因 |
| /u/:id | ProfilePage，公开资料+作品/关系 | 昵称不作为身份；停用资料明确不可用；他人不出现收藏页签 |
| /bookmarks | 本人私有分页 | 登录引导；下架项不泄露正文 |
| /publish、/edit/:id、/drafts | EditorPage、DraftsPage | 上传/保存/发布 pending；冲突、失败保留输入；离开确认 |
| /notifications | NotificationPage，分类+已读+定位 | 空消息；不可用目标保留事件说明 |
| /settings/profile、/account、/privacy | SettingsPage，资料/密码/邮箱/注销/关系管理 | 注销密码和独立明确确认；服务器成功才退出 |
| /auth/verify、/auth/reset | 邮件 token 落地页 | pending/有效/过期/已使用；可返回重新申请 |
| /admin/... | 独立 AdminConsole，审核/举报/申诉/用户/审计 | 鉴权完成再判断；无权限显示403且无写按钮 |

旧 /profile?userId=id 映射 /u/id；本人 menu 对应作品/收藏/评论/通知/设置。旧 /detail 链接保持。URL query 只存可分享筛选，不放密码/正文；邮件 token 处理成功后从地址栏移除。

## 发现与关注线框

发现：左导航 | 顶搜（最大560px）+发布；标题/推荐热门最新 tabs；内容区 CSS grid，卡片220–280px；1440约4列，1024约3列，768约2列，390两列，<360可一列。DOM按服务端顺序，禁止 columns 破坏键盘顺序。卡片封面固定比例4:5（内含图片可object-fit:cover），lazy loading+width/height占位；标题最多两行；作者头像昵称；点赞是独立button，不能嵌在链接内或传播点击到详情。纯文卡片以标题+真实摘要构成自然留白，无假图和装饰统计；长昵称截断，完整名称有可访问文本。

关注：最大720px单列，头像/作者/时间→标题正文摘要→最多3张预览（显示总图数）→点赞/评论/收藏；同样使用实体状态与操作。空关注引导去发现，错误可局部重试。

## 详情和媒体

从列表点击：history state 保存 background route、query、scrollY、触发元素；URL变为 /detail/id，列表保留原组件和已加载页。桌面 dialog 约 min(1200px,92vw)、90vh，左图55%右文/评论45%，各有合理滚动边界；无图用最大760px阅读布局。直达或刷新不使用内存背景，完整页相同实体接口。手机统一全屏，顶部返回/作者，图组→正文→互动→评论，不横向溢出。关闭有背景时 back；无背景去发现/合理来源。前进恢复详情；返回列表还原 query 和滚动。

查看器独立最上层：上一/下一、计数、缩放、关闭、图片错误重试，左右键/双指或按钮缩放、滑动切图。Esc只关闭最上层，关闭后焦点返回触发图；详情关闭后返回触发卡片；背景 inert、滚动锁，Tab受约束；所有按钮可访问命名。目标变不可用停止正文/互动呈现，显示明确状态。

## 创作、讨论与消息

保留 Quill 富文本；标题、正文、标签、媒体托盘、保存状态/草稿、发布区域层级明确。媒体项有缩略/进度/排序/移除/取消/重试；仍上传或失败禁止发布。保存请求串行/版本化，状态显示“保存中/已保存时间/保存失败”；输入改变后 pending 不得覆盖更晚输入；同一发布 requestKey 重试不重复，服务器确认才清空跳转。本地恢复按账户隔离且退出清理，仅为失败备份。

评论：最新/热门 tabs、总数取服务端；根评论分页、两级回复、@对象与取消回复；“展开更多回复”按根独立分页。失败保留输入；会话过期弹登录并保留输入，成功后由用户再点发送。删除父节点展示不可用占位并保留合法回复，旧正文不可见。定位 commentId 时按实体/根读取，不能只在第一页查找。

通知：全部/互动/系统，未读点+可读文字，单条/全部已读，点击目标/评论；页面可见时轮询，隐藏退出停止。历史目标失效保留事件说明；不展示不再可见的正文快照。资料和关系页按tab独立分页，加载更多不跨tab串数据。

## 各页统一状态与交互验收

每个上述页面都要有 loading（与布局等高骨架，aria-busy）、empty（真实描述+有用入口）、error（保留既有内容+重试）、forbidden（登录或权限说明）、deleted/unavailable（不返回旧正文）。没有适用删除实体的列表以过滤结果/空态呈现；设置/创作不伪造 deleted 状态。按钮请求中禁重复，成功以服务器结果反馈，失败保留输入。危险操作先明确列后果并确认；不用 window.alert/空按钮/开发中代替业务。

检查1440/1024/768/390px：导航不遮正文、底栏不遮提交、滚动无横向溢出、软键盘不盖评论输入、多图/纯文/长标题/缺头像稳定；200%缩放可用。键盘能导航卡片、点赞、开关详情/查看器、回复、提交；快捷键避开 input/textarea/contenteditable 与 event.isComposing。视觉检查必须记录实际截图路径与实际行为，构建通过不能当作浏览器验收。


## 实现记录

App.vue现只协调会话、实体更新、路由背景与公共动作，页面用defineAsyncComponent按需加载。FeedPage/SearchPage保留背景列表，详情关闭不重置分页；只有本次运行访问过的列表允许背景弹层，刷新/新窗口为完整页。Element Plus管理焦点约束、返回焦点、背景锁滚动与嵌套弹窗Esc。390px详情全屏；图片查看器有按钮缩放、左右键、切图滑动及双指缩放逻辑。

导航与图标采用项目内SVG组件，去除旧emoji Logo、大渐变导航、装饰统计、静态mock和Vue调试浮层。正文/图片/作者都有真实缺失或失败状态；列表按DOM顺序CSS grid。时间显示月日，datetime保留ISO，避免关注页长时间戳挤压。

已实际检查发现页1440/1024/768/390px及390px十二个社区页面；所有页面宽度检查未见横向溢出。桌面路由弹层和嵌套图片焦点已实际检查；硬件手机软键盘与双指手势未在实体设备执行，不能以桌面视口替代。构建按页分包已完成，Element Plus公共包体积提示保留。
