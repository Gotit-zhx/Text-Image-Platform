<h1 align="center">百草园 · Baicaoyuan</h1>

<p align="center">记录生活，分享图文，让有趣的内容与人相遇。</p>

<p align="center">
  <a href="https://github.com/Gotit-zhx/Text-Image-Platform/actions/workflows/ci.yml"><img src="https://github.com/Gotit-zhx/Text-Image-Platform/actions/workflows/ci.yml/badge.svg?branch=master" alt="CI 工作流状态" /></a>
  <img src="https://img.shields.io/badge/Vue-3-42b883?logo=vuedotjs&logoColor=white" alt="Vue 3" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178c6?logo=typescript&logoColor=white" alt="TypeScript 5" />
  <img src="https://img.shields.io/badge/Django-5.2-092e20?logo=django&logoColor=white" alt="Django 5.2" />
</p>

<p align="center">
  <a href="#功能概览">功能</a> ·
  <a href="#界面截图">界面截图</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#本地开发">本地开发</a> ·
  <a href="#文档">文档</a> ·
  <a href="#参与贡献">参与贡献</a>
</p>

**百草园（TIP / Text-Image-Platform）** 是使用 Vue 3、TypeScript 与 Django 构建的图文社区，覆盖发现内容、发布创作、评论互动、关注收藏、消息通知和社区治理。一个前端同时适配 PC 与移动浏览器，支持本地开发与 Docker Compose 自托管。

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">发现：图文瀑布流</th></tr>
  <tr>
    <td><a href="docs/assets/readme/discover-desktop.jpg"><img src="docs/assets/readme/discover-desktop.jpg" alt="发现：图文瀑布流：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/discover-mobile.jpg"><img src="docs/assets/readme/discover-mobile.jpg" alt="发现：图文瀑布流：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

## 功能概览

| 模块 | 当前能力 |
| --- | --- |
| 内容发现 | 图文瀑布流、推荐 / 热门 / 最新排序、关注动态、帖子 / 用户 / 标签搜索 |
| 阅读互动 | 独立详情页与详情弹层、多图查看与缩放、评论与回复、点赞、收藏、分享 |
| 个人空间 | 公开主页、本人作品管理、评论记录、粉丝与关注列表 |
| 图文创作 | 富文本编辑、图片上传与排序、标签、草稿自动保存、本地失败恢复、作品编辑 |
| 账号安全 | 注册登录、邮箱验证、密码重置与修改、个人资料、账号注销 |
| 通知与治理 | 持久化通知、拉黑 / 屏蔽、举报、申诉，以及管理侧审核、角色权限与审计记录 |
| 部署与维护 | Compose 编排、持久化数据库 / 媒体、健康检查、备份恢复指引、GitHub Actions |

> **推荐模块的范围：** 当前社区信息流使用内容热度规则；仓库另提供 ALS 数据处理与离线训练代码。模型在线服务与生产级个性化推荐仍在迭代。

## 界面截图

以下 **30 组、60 张截图** 均来自实际运行的用户侧页面，覆盖 PC 和移动浏览器布局。发现页见首屏，其余界面按使用流程分组展开；点击任意截图可查看原图。

- **PC 视口：** 1440 × 1000；**移动浏览器视口：** 390 × 844。
- **移动端说明：** 展示响应式 Web 页面，截图来自浏览器视口，不代表实体手机或原生 App 验收。
- **内容说明：** 使用隔离的本地演示数据库。人物、图文、评论、通知与草稿均为示例，不代表真实用户或线上活跃度；空列表保留产品实际空状态。
- **素材说明：** 配图是已下载的 Wikimedia Commons 公开许可图片，没有使用 AI 生成图片；[原始来源与许可](docs/demo-media-sources.md)随仓库提供。

<details>
<summary><strong>浏览与搜索</strong> · 3 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">关注动态</th></tr>
  <tr>
    <td><a href="docs/assets/readme/following-desktop.jpg"><img src="docs/assets/readme/following-desktop.jpg" alt="关注动态：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/following-mobile.jpg"><img src="docs/assets/readme/following-mobile.jpg" alt="关注动态：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">帖子与标签搜索</th></tr>
  <tr>
    <td><a href="docs/assets/readme/search-posts-desktop.jpg"><img src="docs/assets/readme/search-posts-desktop.jpg" alt="帖子与标签搜索：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/search-posts-mobile.jpg"><img src="docs/assets/readme/search-posts-mobile.jpg" alt="帖子与标签搜索：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">用户搜索</th></tr>
  <tr>
    <td><a href="docs/assets/readme/search-users-desktop.jpg"><img src="docs/assets/readme/search-users-desktop.jpg" alt="用户搜索：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/search-users-mobile.jpg"><img src="docs/assets/readme/search-users-mobile.jpg" alt="用户搜索：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

<details>
<summary><strong>阅读与互动</strong> · 4 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">信息流中的作品详情弹层</th></tr>
  <tr>
    <td><a href="docs/assets/readme/post-dialog-desktop.jpg"><img src="docs/assets/readme/post-dialog-desktop.jpg" alt="信息流中的作品详情弹层：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/post-dialog-mobile.jpg"><img src="docs/assets/readme/post-dialog-mobile.jpg" alt="信息流中的作品详情弹层：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">可直接访问的图文详情页</th></tr>
  <tr>
    <td><a href="docs/assets/readme/post-detail-desktop.jpg"><img src="docs/assets/readme/post-detail-desktop.jpg" alt="可直接访问的图文详情页：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/post-detail-mobile.jpg"><img src="docs/assets/readme/post-detail-mobile.jpg" alt="可直接访问的图文详情页：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">评论与讨论</th></tr>
  <tr>
    <td><a href="docs/assets/readme/comments-desktop.jpg"><img src="docs/assets/readme/comments-desktop.jpg" alt="评论与讨论：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/comments-mobile.jpg"><img src="docs/assets/readme/comments-mobile.jpg" alt="评论与讨论：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">多图浏览与缩放</th></tr>
  <tr>
    <td><a href="docs/assets/readme/image-viewer-desktop.jpg"><img src="docs/assets/readme/image-viewer-desktop.jpg" alt="多图浏览与缩放：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/image-viewer-mobile.jpg"><img src="docs/assets/readme/image-viewer-mobile.jpg" alt="多图浏览与缩放：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

<details>
<summary><strong>个人空间与关系</strong> · 7 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">他人的公开主页</th></tr>
  <tr>
    <td><a href="docs/assets/readme/profile-public-desktop.jpg"><img src="docs/assets/readme/profile-public-desktop.jpg" alt="他人的公开主页：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/profile-public-mobile.jpg"><img src="docs/assets/readme/profile-public-mobile.jpg" alt="他人的公开主页：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">本人主页与作品管理</th></tr>
  <tr>
    <td><a href="docs/assets/readme/profile-self-desktop.jpg"><img src="docs/assets/readme/profile-self-desktop.jpg" alt="本人主页与作品管理：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/profile-self-mobile.jpg"><img src="docs/assets/readme/profile-self-mobile.jpg" alt="本人主页与作品管理：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">我的评论记录</th></tr>
  <tr>
    <td><a href="docs/assets/readme/profile-comments-desktop.jpg"><img src="docs/assets/readme/profile-comments-desktop.jpg" alt="我的评论记录：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/profile-comments-mobile.jpg"><img src="docs/assets/readme/profile-comments-mobile.jpg" alt="我的评论记录：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">粉丝列表</th></tr>
  <tr>
    <td><a href="docs/assets/readme/profile-followers-desktop.jpg"><img src="docs/assets/readme/profile-followers-desktop.jpg" alt="粉丝列表：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/profile-followers-mobile.jpg"><img src="docs/assets/readme/profile-followers-mobile.jpg" alt="粉丝列表：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">关注列表</th></tr>
  <tr>
    <td><a href="docs/assets/readme/profile-following-desktop.jpg"><img src="docs/assets/readme/profile-following-desktop.jpg" alt="关注列表：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/profile-following-mobile.jpg"><img src="docs/assets/readme/profile-following-mobile.jpg" alt="关注列表：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">我的收藏</th></tr>
  <tr>
    <td><a href="docs/assets/readme/bookmarks-desktop.jpg"><img src="docs/assets/readme/bookmarks-desktop.jpg" alt="我的收藏：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/bookmarks-mobile.jpg"><img src="docs/assets/readme/bookmarks-mobile.jpg" alt="我的收藏：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">消息通知</th></tr>
  <tr>
    <td><a href="docs/assets/readme/notifications-desktop.jpg"><img src="docs/assets/readme/notifications-desktop.jpg" alt="消息通知：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/notifications-mobile.jpg"><img src="docs/assets/readme/notifications-mobile.jpg" alt="消息通知：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

<details>
<summary><strong>图文创作</strong> · 4 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">发布图文：标题、配图与编辑器</th></tr>
  <tr>
    <td><a href="docs/assets/readme/publish-desktop.jpg"><img src="docs/assets/readme/publish-desktop.jpg" alt="发布图文：标题、配图与编辑器：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/publish-mobile.jpg"><img src="docs/assets/readme/publish-mobile.jpg" alt="发布图文：标题、配图与编辑器：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">发布图文：正文、标签与保存发布</th></tr>
  <tr>
    <td><a href="docs/assets/readme/publish-tools-desktop.jpg"><img src="docs/assets/readme/publish-tools-desktop.jpg" alt="发布图文：正文、标签与保存发布：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/publish-tools-mobile.jpg"><img src="docs/assets/readme/publish-tools-mobile.jpg" alt="发布图文：正文、标签与保存发布：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">编辑已发布作品</th></tr>
  <tr>
    <td><a href="docs/assets/readme/edit-post-desktop.jpg"><img src="docs/assets/readme/edit-post-desktop.jpg" alt="编辑已发布作品：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/edit-post-mobile.jpg"><img src="docs/assets/readme/edit-post-mobile.jpg" alt="编辑已发布作品：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">草稿箱</th></tr>
  <tr>
    <td><a href="docs/assets/readme/drafts-desktop.jpg"><img src="docs/assets/readme/drafts-desktop.jpg" alt="草稿箱：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/drafts-mobile.jpg"><img src="docs/assets/readme/drafts-mobile.jpg" alt="草稿箱：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

<details>
<summary><strong>资料与账号</strong> · 3 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">编辑个人资料</th></tr>
  <tr>
    <td><a href="docs/assets/readme/edit-profile-desktop.jpg"><img src="docs/assets/readme/edit-profile-desktop.jpg" alt="编辑个人资料：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/edit-profile-mobile.jpg"><img src="docs/assets/readme/edit-profile-mobile.jpg" alt="编辑个人资料：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">账号设置</th></tr>
  <tr>
    <td><a href="docs/assets/readme/settings-account-desktop.jpg"><img src="docs/assets/readme/settings-account-desktop.jpg" alt="账号设置：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/settings-account-mobile.jpg"><img src="docs/assets/readme/settings-account-mobile.jpg" alt="账号设置：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">隐私与关系管理（空状态）</th></tr>
  <tr>
    <td><a href="docs/assets/readme/settings-privacy-desktop.jpg"><img src="docs/assets/readme/settings-privacy-desktop.jpg" alt="隐私与关系管理（空状态）：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/settings-privacy-mobile.jpg"><img src="docs/assets/readme/settings-privacy-mobile.jpg" alt="隐私与关系管理（空状态）：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

<details>
<summary><strong>社区治理</strong> · 3 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">举报表单</th></tr>
  <tr>
    <td><a href="docs/assets/readme/report-dialog-desktop.jpg"><img src="docs/assets/readme/report-dialog-desktop.jpg" alt="举报表单：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/report-dialog-mobile.jpg"><img src="docs/assets/readme/report-dialog-mobile.jpg" alt="举报表单：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">我的举报记录（空状态）</th></tr>
  <tr>
    <td><a href="docs/assets/readme/reports-desktop.jpg"><img src="docs/assets/readme/reports-desktop.jpg" alt="我的举报记录（空状态）：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/reports-mobile.jpg"><img src="docs/assets/readme/reports-mobile.jpg" alt="我的举报记录（空状态）：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">我的申诉记录（空状态）</th></tr>
  <tr>
    <td><a href="docs/assets/readme/appeals-desktop.jpg"><img src="docs/assets/readme/appeals-desktop.jpg" alt="我的申诉记录（空状态）：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/appeals-mobile.jpg"><img src="docs/assets/readme/appeals-mobile.jpg" alt="我的申诉记录（空状态）：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

<details>
<summary><strong>登录与注册</strong> · 5 组 PC / 移动端截图</summary>

<table>
  <tr><th width="75%">PC</th><th width="25%">移动浏览器</th></tr>
  <tr><th colspan="2">密码登录</th></tr>
  <tr>
    <td><a href="docs/assets/readme/login-desktop.jpg"><img src="docs/assets/readme/login-desktop.jpg" alt="密码登录：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/login-mobile.jpg"><img src="docs/assets/readme/login-mobile.jpg" alt="密码登录：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">邮箱注册</th></tr>
  <tr>
    <td><a href="docs/assets/readme/register-desktop.jpg"><img src="docs/assets/readme/register-desktop.jpg" alt="邮箱注册：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/register-mobile.jpg"><img src="docs/assets/readme/register-mobile.jpg" alt="邮箱注册：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">密码重置与邮箱验证帮助</th></tr>
  <tr>
    <td><a href="docs/assets/readme/account-help-desktop.jpg"><img src="docs/assets/readme/account-help-desktop.jpg" alt="密码重置与邮箱验证帮助：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/account-help-mobile.jpg"><img src="docs/assets/readme/account-help-mobile.jpg" alt="密码重置与邮箱验证帮助：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">邮件链接入口：重置密码表单</th></tr>
  <tr>
    <td><a href="docs/assets/readme/password-reset-desktop.jpg"><img src="docs/assets/readme/password-reset-desktop.jpg" alt="邮件链接入口：重置密码表单：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/password-reset-mobile.jpg"><img src="docs/assets/readme/password-reset-mobile.jpg" alt="邮件链接入口：重置密码表单：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
  <tr><th colspan="2">邮件链接入口：邮箱验证确认</th></tr>
  <tr>
    <td><a href="docs/assets/readme/email-verify-desktop.jpg"><img src="docs/assets/readme/email-verify-desktop.jpg" alt="邮件链接入口：邮箱验证确认：PC 端实际界面" width="100%" /></a></td>
    <td><a href="docs/assets/readme/email-verify-mobile.jpg"><img src="docs/assets/readme/email-verify-mobile.jpg" alt="邮件链接入口：邮箱验证确认：移动浏览器实际界面" width="100%" /></a></td>
  </tr>
</table>

</details>

## 快速开始

### Docker Compose（推荐用于自托管体验）

需要 Git、Docker Engine 与 Docker Compose v2。

```bash
git clone https://github.com/Gotit-zhx/Text-Image-Platform.git
cd Text-Image-Platform
sh scripts/init-compose.sh
docker compose --env-file .env.compose up -d --build --wait --wait-timeout 120
python3 scripts/check-compose.py
```

打开 **<http://localhost:8080>**。Caddy 提供前端与同源 API，Gunicorn 运行 Django；数据库、媒体与证书使用持久卷，默认仅监听本机。

可选导入社区展示内容：

```bash
docker compose --env-file .env.compose exec app python manage.py seed_demo_data --disable-login
```

该命令生成 9 位示例创作者、12 篇图文，以及评论、点赞、收藏和关注关系；不会自动生成截图中的个人草稿和通知列表。生产模式强制禁用示例账号密码登录，默认关闭注册与邮件入口。容器启动本身不会导入或重置业务数据。

公网域名、HTTPS、SMTP、管理员创建、备份恢复和更新方法见 [部署指南](docs/DEPLOYMENT.md)。

## 本地开发

### 环境要求

- Python **3.11**
- Node.js **20.19+** 或 **22.12+**，以及 npm
- Git

### 安装并启动

```bash
git clone https://github.com/Gotit-zhx/Text-Image-Platform.git
cd Text-Image-Platform
python3.11 -m venv .venv
source .venv/bin/activate
cp .env.example .env
bash run_project.sh --install
```

启动脚本安装前后端依赖、执行数据库迁移并运行开发服务。后续可使用 `bash run_project.sh` 启动，按 `Ctrl+C` 同时停止前后端。

| 服务 | 默认地址 |
| --- | --- |
| Vue / Vite | <http://127.0.0.1:5173> |
| Django API | <http://127.0.0.1:8000> |

本地默认使用 SQLite 与文件媒体存储。环境变量及分别启动前后端的方法见 [开发与运行说明](docs/DEVELOPMENT_GUIDE.md)。

### 导入本地演示内容

保持服务运行，在另一个终端的项目根目录执行：

```bash
cd backend_django
../.venv/bin/python manage.py seed_demo_data
```

命令使用 `demo_assets/` 中的公开图片，重复执行不会新增相同帖子。新建本地演示账号的密码为 `DemoGarden!2026`（例如用户名 `demo_muyu`），仅限本地体验；普通导入不会重置已有账号密码。

只有明确需要重建演示内容时才添加 `--reset`：它会清理演示账号及其内容，保留 staff / superuser。不要对真实业务数据执行演示重建；生产模式始终禁用示例账号密码登录。

## 技术栈与架构

```text
浏览器（PC / 移动 Web）
          │
          ▼
Caddy（Compose：静态前端、同源路由）
          │ /api · /media
          ▼
Django + Gunicorn
          │
          ├── SQLite 持久卷
          └── 本地媒体持久卷

recommend_system/：独立的离线数据处理与 ALS 训练实验
```

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Vue Router、Element Plus、Quill |
| 后端 | Django 5.2、Django REST Framework、Session 认证 |
| 数据与媒体 | SQLite（默认）、Django Storage、Pillow |
| 部署 | Docker Compose、Caddy、Gunicorn |
| 推荐实验 | NumPy、Pandas、SciPy、scikit-learn、implicit、Optuna |
| 自动检查 | GitHub Actions、Django 测试、前端类型检查与构建、Compose 冒烟检查 |

Web 镜像只安装运行社区所需依赖，不安装推荐训练依赖。推荐实验的运行方式见 [开发文档](docs/DEVELOPMENT_GUIDE.md)。

### 项目结构

```text
Text-Image-Platform/
├── frontend_vue/         # Vue 用户界面与管理界面
├── backend_django/       # Django API、社区业务、管理命令与迁移
├── recommend_system/     # 数据处理与离线推荐训练
├── demo_assets/          # 公开许可的演示配图
├── deploy/               # Dockerfile、Caddy、Gunicorn 与容器入口
├── scripts/              # Compose 初始化、备份与健康检查
├── docs/                 # 公开使用指南、API 契约与 UI 规范
│   └── assets/readme/    # 用户侧 PC / 移动端截图
├── .github/workflows/    # CI
├── compose.yaml          # 自托管演示站编排
├── requirements.txt      # Python 依赖
├── run_project.sh        # 本地启动脚本
└── .env.example          # 无密钥环境变量模板
```

## 测试与构建

在项目根目录激活虚拟环境后，运行后端测试：

```bash
source .venv/bin/activate
cd backend_django
python manage.py test
```

在另一个终端的项目根目录执行前端检查：

```bash
cd frontend_vue
npm ci
npm test
```

`npm test` 执行 TypeScript 检查与生产构建。GitHub Actions 还会运行 Django 迁移与测试，并构建、启动 Compose 栈检查健康状态和同源路由；顶部 CI 徽章链接到实际工作流结果。

## 文档

| 文档 | 内容 |
| --- | --- |
| [文档索引](docs/README.md) | 阅读顺序、目录约定与提交范围 |
| [快速开始](docs/QUICK_START.md) | 开发环境安装与首次运行 |
| [部署指南](docs/DEPLOYMENT.md) | Compose、域名、HTTPS、SMTP、备份与更新 |
| [开发与运行说明](docs/DEVELOPMENT_GUIDE.md) | 环境变量、启动方式、推荐训练与 CI |
| [项目概览](docs/PROJECT_OVERVIEW.md) / [详细说明](docs/PROJECT_DETAILS.md) | 业务模块、数据模型与项目组织 |
| [API 契约](docs/API_CONTRACT.md) | 认证、权限、接口、错误响应与状态规则 |
| [UI 规范](docs/UI_SPEC.md) | 设计变量、布局、组件与交互约定 |
| [图片来源与许可](docs/demo-media-sources.md) | 演示素材的原始来源与使用许可 |

## 项目状态

本项目处于持续开发阶段，当前仓库提供可运行的社区业务、管理与治理流程、自托管配置和自动化检查。以下工作仍需持续完善：

- 实体手机、辅助技术与完整人工场景验收。
- 自有服务器上的 HTTPS、真实邮件送达与公网部署验收。
- 并发容量、生产运行监控与推荐模型在线化。

截图展示当前版本的真实界面与示例数据，不作为上述能力已完成验收的证明。

## 参与贡献

欢迎通过 [Issues](https://github.com/Gotit-zhx/Text-Image-Platform/issues) 报告问题或讨论功能，通过 Pull Request 提交改进。

- 问题反馈请提供复现步骤、预期与实际表现；界面问题请附浏览器版本、视口尺寸和脱敏截图。
- 代码改动请保持现有 API 契约与设计变量一致，运行相关测试，并同步维护使用文档。
- 数据库、上传文件、环境密钥、开发邮件与测试产物不提交。开发提示词、任务清单和验收笔记统一放入已被 Git 忽略的 `docs/local/`。

## 许可与致谢

仓库目前未提供项目代码的 `LICENSE` 文件，不宣称代码采用某一开源协议。演示图片的许可单独记录在 [素材来源文档](docs/demo-media-sources.md)，第三方依赖与素材分别遵循各自许可。

感谢 Vue、Django、Element Plus、Quill 等项目，以及 Wikimedia Commons 的公开素材贡献者。
