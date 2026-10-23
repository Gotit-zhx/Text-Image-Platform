# 百草园 API 与业务契约

日期：2026-10-22。基线与实施契约：T00现状映射保留为历史依据；下方接口已随T01–T09实现，实际验证见IMPLEMENTATION_REPORT与ACCEPTANCE_SCENARIOS。

## 现状复核与阶段依赖

| 阶段 | 直接依赖 | 可复用 | 缺失/待修复 |
| --- | --- | --- | --- |
| T01 | T00 | Django User、Session、密码验证器、登录弹窗 | 请求内管理员重置、自动注册、默认密码、邮箱重复、公开隐私、CSRF、邮件/改密/注销 |
| T02 | T00/T01 | HomePostCard、Element Plus、路由 | 统一 tokens/AppShell、卡片/时间线、页面拆分 |
| T03 | T01/T02 | Post、分页 search/recommend、编辑接口 | GET 详情、软删除、摘要 DTO、统一可见性、服务端净化、取消全站 bootstrap 依赖 |
| T04 | T03 | Quill、发布/编辑 | Media、上传、草稿、幂等提交、成功后清空 |
| T05 | T03/T04 | /detail/:id、DOMPurify | 路由背景弹层、图片查看器、焦点/滚动恢复 |
| T06 | T03/T05 | Comment、CommentLike | 单帖/本人分页、root/parent/replyTo、占位、服务端排序 |
| T07 | T03/T04/T06 | Follow、公开资料路由、搜索 | 稳定主页、独立关系/收藏分页、用户搜索、拉黑/屏蔽 |
| T08 | T01/T03/T06/T07 | AuditLog 历史通知、互动关系 | Notification、未读/已读、事件去重、服务端计数校正 |
| T09 | T03/T06/T07/T08 | 审核接口、组、审计 | 举报/申诉、角色授权、禁言封禁、最后超管保护、活跃口径 |
| T10 | T02–T09 | 各页组件 | 四断点实际视觉检查、键盘/IME、请求取消、统一状态 |
| T11 | T01–T10 | Django 13 项测试、npm test | F01–F08 隔离业务与浏览器验证、迁移演练 |

源码证据：community/views.py 的 _ensure_default_admin 被 bootstrap/recommend/admin login 调用；register 接受缺密码；login 自动创建邮箱账号；公开 profile 返回本人 DTO；写接口 csrf_exempt。posts/:id 当前仅 PUT；评论取全站 50 条且不关联帖子审核过滤；fans 截断 30；评论总数被前端局部集合覆盖。发布和评论组件在服务端确认前清空。审核靠 is_staff，活跃统计按帖子日期。审查中的 ALS 重载问题在 trainer.py 仍读取未恢复的 train_mat；本轮规则回退可交付，不要求修复推荐训练基础设施。基线后端 13 项测试通过，仅说明旧测试通过。

## 传输、错误与分页

根路径 /api，无末尾斜杠；Session Cookie，写请求必须 X-CSRFToken。GET /auth/csrf 返回 token，登录轮换后重新取得。读请求不得创建账号、资料、内容或改凭证。JSON 对象请求，字段类型错误返回 400，不把解析失败当默认值。

现有 envelope：`{"code":0,"message":"ok","data":{},"requestId":"..."}`。错误：相同结构、data=null；400 参数，401 未登录/凭证无效，403 CSRF/权限/禁言，404 不存在或不可公开目标，409 重复邮箱/冲突/重复举报，413 超限，429 频率限制。服务端日志用 requestId 关联，禁止向客户端泄露异常堆栈。

列表统一 `{"items":[],"pagination":{"page":1,"pageSize":20,"total":0,"hasMore":false}}`；保留现有 search/recommend 的 posts 键兼容旧客户端。page>=1、pageSize 1–50；顺序以时间+id 或热度+时间+id 稳定排序。前端追加按实体 id 去重；更换 query 取消旧请求并归零分页。所有新 DTO 时间为含时区 ISO 8601（createdAt/updatedAt/readAt），不按 MM-DD 字符串排序；旧 time/date 只兼容显示。

通知支持 `GET /notifications?category=system&beforeId=123&pageSize=20`。category为空表示全部，social为互动，system为系统；按createdAt、id倒序。beforeId必须是本人当前分类内已存在通知的十进制ID（最多19位），非法、其他接收者或其他分类锚点返回400。游标返回严格早于该通知的记录；使用游标时page保持1，pagination.total为当前游标之后的记录数。原page分页继续兼容旧客户端。新前端以最后一条ID加载更早记录；刷新从最新端逐页读取，直到与已加载ID相交或读完，合并时保留历史页和已读状态，避免一次新增超过20条时漏读。单条/全部已读会使先前刷新响应失效，切分类取消旧请求。

## 接口表

下表按最终路由核对；bootstrap仅保留旧客户端兼容。

| 方法 /api 路径 | T00 状态 | 权限/用途 | 阶段 |
| --- | --- | --- | --- |
| POST /auth/register, /auth/login, /auth/logout | 已实现，保留兼容 | 注册/登录/退出；注册改为等待验证 | T01 |
| GET /users/me; PUT /users/me/profile | 已实现，保留兼容 | 本人 DTO/资料 | T01/T07 |
| GET /auth/csrf | 已实现 | 匿名取得 CSRF | T01 |
| POST /auth/verify-email, /auth/resend-verification | 已实现 | token、重发 | T01 |
| POST /auth/password-reset, /auth/password-reset/confirm | 已实现 | 通用发送响应、token+新密码 | T01 |
| POST /users/me/password, /users/me/deactivate | 已实现 | 旧密码；注销二次确认 | T01 |
| GET /community/bootstrap | 旧兼容，新页面不依赖 | 旧初始化快照兼容 | T03 |
| GET /community/search, /community/recommend, /community/recommend/status | 已实现，保留兼容 | 分页发现/搜索/推荐状态；搜索扩展 type=users/tag | T03/T07 |
| POST /community/posts; PUT /community/posts/:id | 已实现，保留兼容 | 作者发布/编辑 | T03/T04 |
| GET/DELETE /community/posts/:id | 已实现 | 公开详情/本人软删 | T03 |
| GET /community/users/:id/profile | 已实现，保留兼容 | 公开资料，剔除隐私 | T01/T07 |
| GET /community/users/:id/posts, /followers, /following | 已实现 | 公开作品和关系完整分页 | T03/T07 |
| GET /users/me/posts, /bookmarks, /comments | 已实现 | 本人创作/私有收藏/历史 | T03/T06/T07 |
| POST /community/posts/:id/comments | 已实现，保留兼容 | 公开目标、回复关系、幂等键 | T06 |
| GET /community/posts/:id/comments | 已实现 | sort=latest/hot，按根分页 | T06 |
| GET /community/comments/:id/replies, /community/comments/:id/detail | 已实现 | 同根回复完整分页 | T06 |
| POST /community/comments/:id/like; DELETE /community/comments/:id | 已实现，保留兼容 | 可见评论点赞/本人软删 | T06 |
| POST /community/posts/:id/like, /favorite, /read, /share | 已实现，保留兼容 | true/false 为期望状态，返回权威计数 | T03/T08 |
| POST /community/authors/:id/follow | 已实现，保留兼容 | 期望状态、禁止自己/双向拉黑 | T07 |
| POST /media; DELETE /media/:id | 已实现 | multipart、本人未引用资源 | T04 |
| GET/POST /drafts; GET/PUT/DELETE /drafts/:id | 已实现 | 仅本人，自动保存/继续编辑 | T04 |
| GET/POST /users/me/blocks, /users/me/mutes; DELETE /users/me/blocks/:id, /users/me/mutes/:id | 已实现 | 本人关系管理 | T07 |
| GET /notifications, /notifications/unread; POST /notifications/:id/read, /notifications/read-all | 已实现 | 本人、分类、已读 | T08 |
| POST/GET /reports; POST/GET /appeals | 已实现 | 举报/申诉及本人记录 | T09 |
| POST /admin/auth/login, /logout; GET /admin/auth/me | 已实现，保留兼容 | 管理会话；须校验凭证版本 | T01/T09 |
| GET /admin/dashboard/overview | 已实现，保留兼容 | 移除错误活跃统计 | T09 |
| GET /admin/moderation/posts, /posts/:id; POST /posts/:id/review, /posts/batch-review | 已实现，保留兼容 | 队列、详情、审核 | T09 |
| GET /admin/moderation/comments; POST /comments/:id/hide, /restore; DELETE /comments/:id | 已实现，保留兼容 | 评论治理 | T06/T09 |
| GET /admin/users; PUT /admin/users/:id/roles; GET /admin/audit/logs | 已实现，保留兼容 | 用户、仅超管改角色、审计 | T09 |
| GET /admin/reports, /admin/appeals; POST /admin/reports/:id/resolve, /admin/appeals/:id/resolve, /admin/users/:id/status | 已实现 | 处置与反馈、禁言/封禁/解封 | T09 |

## DTO 和请求示例（当前形态）

PublicUser：id, name（昵称，与登录用户名独立）, avatarText, avatarUrl, signature, fans, follows, totalLikes, isFollowing, isBlocked, isMuted。绝不含 email、roles、isAdmin、gender 等本人字段。SelfUser 额外 email, emailVerified, gender, roles, isAdmin。保持 Django User 主键，不修改 AUTH_USER_MODEL。

PostSummary：id,title,summary,authorId,author,authorAvatarUrl,createdAt,updatedAt,tags,images（兼容 URL 列表）,media（id,url,thumbnailUrl,width,height,size）,likes,comments,isLiked,isFavorited,isFollowingAuthor；不包含 contentHtml。PostDetail 加 contentHtml；reviewReason、非公开状态只给作者创作管理和授权管理端。新写入资源用 mediaIds（最多 9），服务器按顺序解析，不能引用他人私有媒体。

```json
{"title":"山野记录","summary":"","contentHtml":"<p>今天的记录</p>","tags":["日常"],"mediaIds":[12,15],"requestKey":"客户端每次创作生成并在重试时保留的 UUID"}
```

PUT 的未提供字段保持；summary/tags/mediaIds 显式空值（空字符串/空数组）清空；title 必填非空 <=255，summary<=500，正文<=100000 字符，标签最多5个、各<=24，图片最多9个。HTML 服务端白名单：段落、列表、标题、强调、引用、受控链接和图片；去脚本/事件/style/危险协议；DOMPurify 为第二层防护。旧 base64 仅历史读取，编辑时仅允许保留原有旧资源，不新增 data URL。

Comment：id,postId,authorId,author,content,createdAt,likes,isLiked,isMine,parentId,rootId,replyToId,replyToName,deleted,replyCount。根 parent/root/replyTo 为空；回复保存直接 parent 和根 root，replyTo 标识明确对象。展示两级，回复任意子评论仍挂同一根。删除/隐藏/停用的父节点只返回占位，无旧正文/私密作者信息；不可回复占位。创建请求 `{content,replyToId:null,requestKey}`，正文 1–2000。

Media（已实现）：owner、Storage 路径、thumbnail、真实格式、宽高、字节数、createdAt；JPEG/PNG/WebP/GIF（首版 GIF 静态缩略），每张<=10MiB、<=4000万像素、每帖<=9；不信 MIME/扩展名。上传先验证再存储，清 EXIF；引用资源不可直接删；未引用资源至少24小时后由显式清理命令回收，草稿引用受保护。

Draft（已实现）：id,title,contentHtml,tags,mediaIds,updatedAt,version；owner 私有；保存携带 version，冲突409并保留输入；发布使用 requestKey，重试返回同一帖。同 key 不同正文409。草稿自动保存防乱序。

Notification（已实现）：id,event,actor（公开最小资料）,targetType,targetId,postId,commentId,snapshot,unavailable,createdAt,readAt；删除目标仍保留事件类型/时间；快照不得绕过目标可见性泄露正文。审计不直接兼作通知。

## 权限与可见性矩阵（目标规则）

| 操作 | 游客 | 正常用户 | 禁言 | 封禁/注销 | 审核员 | 运营 | 审计员 | 超管 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 公开浏览/搜索/资料 | 是 | 是 | 是 | 按游客 | 是 | 是 | 是 | 是 |
| 发布/编辑/回复/社交互动 | 登录 | 本人/可见目标 | 否 | 否 | 同普通用户 | 同普通用户 | 同普通用户 | 同普通用户 |
| 私有草稿/收藏/账号设置 | 否 | 本人 | 本人可管理 | 否 | 本人 | 本人 | 本人 | 本人 |
| 内容队列/审核/评论处置 | 否 | 否 | 否 | 否 | 读写 | 只读 | 只读 | 读写 |
| 举报/申诉处置、用户禁言封禁 | 否 | 否 | 否 | 否 | 内容举报/申诉 | 账号处置/举报 | 只读 | 全部 |
| 用户私人邮箱/角色调整 | 否 | 否 | 否 | 否 | 无邮箱 | 无邮箱 | 无邮箱 | 读写 |
| 审计 | 否 | 否 | 否 | 否 | 自身处置记录 | 自身处置记录 | 只读全部 | 读全部 |

super_admin 组不能单独提权为真正超管；is_superuser 为最终角色授权依据。最后一个活跃超管禁止降级/封禁/注销。旧 is_staff 无组账号只给只读权限，运行显式授权命令迁移，不能请求时自动升权。

公开帖子统一 approved && deletedAt=null && author.is_active。作者创作管理可看本人其他状态；公共详情不返回非公开正文。评论、互动、推荐、搜索、收藏统一检查目标。屏蔽只从本人发现/关注/推荐消费中排除；拉黑双向禁止新增关注/评论/通知并解除既有关注，从登录消费中排除；匿名仍能访问公共帖，不是隐私屏障。

## 状态转换和事件

帖子：正常发布→approved；正常编辑→approved（updatedAt更新）；审核→pending/approved/rejected/offline；驳回/下架编辑→仍保持原状态，显式提交复核→pending；只有授权审核可恢复 approved。本人删除→deletedAt，不可复活。草稿发布后才创建帖子。

评论：visible→hidden（审核可恢复）、visible/hidden→deleted（不可恢复正文）；子回复保留合法上下文，计数仅计算可见有效正文。账号：新注册→待验证→正常；正常↔禁言，正常/禁言↔封禁；正常→注销（停用/匿名化/会话撤销），不执行硬删关联和审计。

邮箱验证与重置 token：仅存摘要、有效期、用途、使用时间；验证24小时、重置1小时，单次使用；重发间隔60秒；发送接口始终通用响应，不暴露账号存在；开发显示“请求已处理，请查看本地邮件输出”，不宣称已送达。重置改密码使所有旧会话失效；改密验证旧密码，当前会话更新认证 hash，其余失效；管理员独立会话也必须验证认证 hash。注销需 password + confirmation，停用、公开匿名化、清空敏感资料；仅独立测试账号执行验收。

| 事件 | 接收者 | 去重键/限制 |
| --- | --- | --- |
| post.like | 帖子作者 | interaction id；同一关系仅保留一条点赞通知，反复取消/重赞不刷屏 |
| follow | 被关注者 | follow id；不重复/self/拉黑 |
| comment/reply | 作者/被回复者（同接收者只一条） | comment id + recipient |
| post.review/comment.moderation | 被处置作者 | audit id + recipient |
| report.resolved/appeal.resolved | 举报人/申诉人/被处置作者 | 决议 id + recipient |

收藏不通知作者；自己不通知自己；创建事件与业务事务一起落库，拉黑禁止新通知，历史可见性随目标实时计算。通知页可见时30秒轮询未读，隐藏/退出停止。

## 渐进迁移和数据保护

1. 保留所有现有迁移和 Django User。先独立数据库备份、隔离恢复演练；不在业务数据库做 destructive 验收。
2. 邮箱先用只读 audit 命令报告规范化后重复/空/非法邮箱（输出限制，文件不入库）。无冲突者回填一对一身份记录，并对 lower(trim(email)) 非空建立数据库唯一保护。存在冲突时迁移明确停止，保留账号和归属；由用户审阅选择实际归属、更换并验证邮箱，绝不自动合并/删账号/重置密码。空邮箱保留可按用户名登录的历史账号，绑定时验证。
3. Profile 增加昵称/简介并按旧 username 回填，公开渲染优先 nickname；User.username、User.id、外键不变。现有账号邮箱默认未验证但允许历史凭证登录，提示验证；新注册验证后登录。不得批量撤销历史账号凭证。
4. Post 新增 deletedAt；旧 approved/pending/rejected/offline 保留；Comment 新关系可空、旧评论都是根节点。新增媒体与草稿/通知/治理模型，旧 JSON/images/content_html 保留原样。
5. 旧 base64 直接兼容阅读，不塞进新列表摘要；后续独立命令 dry-run→复制到 Storage→记录原图映射/校验→选择性转换，保留原文备份与回滚，不覆盖原始文件。渐变演示封面作为无图处理。
6. /detail/:id 永久沿用；/profile?userId=... 或旧本人菜单映射稳定 /u/:id 和设置/收藏/通知页，query 不含隐私；直达详情独立 GET，旧 bootstrap 暂保留不再用于新页。
7. 历史审计通知独立一次性迁移，source audit id 唯一；缺失目标仍保留历史事件并标 unavailable，不猜测已删除评论的原作者。不删除审计，不重新发送历史社交通知。

当前实现补充：
- 自己的作品管理使用 GET /community/posts/:id?manage=1；公共详情不公开offline/rejected正文。提交复核为 POST /community/posts/:id/resubmit。
- Profile.avatar_media关联已上传头像，防清理误删与跨用户引用；公开头像通过同一媒体读取接口鉴权。
- 草稿与作品媒体顺序以images URL列表为权威，DTO media/mediaIds按相同顺序返回；本地恢复仅保存账号隔离的输入和资源ID。
- 先发后审保持approved；编辑被处置作品不自恢复。处置原因、申诉结果持久化并接入通知，审核通知返回作者manageUrl。
- 通知DTO不返回正文快照；快照只存治理原因。点赞每段关系一条通知，收藏不通知。历史通知迁移0010仅对可追溯接收者生成audit:ID唯一键，无法追溯的删除目标不猜作者。
- 邮箱验证24小时/重置1小时；通用邮件响应、IP限频与每账号60秒重发冷却。AuthAttempt仅存散列key，未落原IP；定期清理可另行维护。
- 当前SQLite使用迁移0005的表达式唯一索引保护User邮箱；空邮箱历史账号保留。非SQLite正式迁移不在本轮范围。
- MIME输出JPEG/PNG，原GIF首版转静态帧；上传文件10MiB、4000万像素、每帖9张。所有存储与清理走FileField Storage。
- 错误code保持HTTP数值；CSRF code=40301；幂等key同内容重试200/原ID，不同内容409。网络错误和超时在前端显示可理解文字，写入不会静默重放。
