# 详细项目说明

## 1. 项目目标

TIP 的目标不是只做一个前端页面或单独的推荐算法脚本，而是把“社区内容产品”和“推荐系统”放进同一个完整工程中。用户可以完成正常的社区互动，系统也可以基于这些互动行为训练模型并返回个性化推荐结果。

这个项目适合用于：

- GitHub 作品集展示
- 课程设计或毕业设计提交
- Vue + Django 全栈项目练习
- 推荐系统工程化落地示例

## 2. 系统组成

### 前端模块

前端位于 `frontend_vue/`，基于 Vue 3、TypeScript 和 Vite 构建，负责：

- 首页信息流
- 帖子详情页
- 发帖与编辑页
- 个人中心
- 管理后台页面
- 调用社区、后台和推荐接口

前端默认通过 Vite 代理将 `/api` 请求转发到 Django，因此第三方本地运行时通常不需要额外处理跨域问题。

### 后端模块

后端位于 `backend_django/`，基于 Django 构建，负责：

- 用户注册、登录、退出和会话恢复
- 社区帖子、评论、关注、互动接口
- 管理端审核与日志接口
- 推荐数据导出与训练命令
- 统一 API 响应结构

后端当前使用 SQLite，适合演示、课程项目和本地运行。后续如果需要上线，可以替换为 PostgreSQL 或 MySQL。

### 推荐系统模块

推荐系统位于 `recommend_system/`，负责：

- 读取交互导出数据
- 构建用户-内容交互矩阵
- 使用 ALS 训练隐式反馈模型
- 保存模型和映射文件
- 为后端在线推荐提供模型文件支持

推荐系统并不是孤立存在的，而是通过 `train_recsys` 命令与业务数据库联通。

## 3. 业务功能说明

### 普通用户功能

- 注册与登录
- 浏览首页内容流
- 查看帖子详情
- 发布与编辑帖子
- 评论帖子
- 点赞、收藏、分享帖子
- 关注作者
- 查看个人主页和个人内容

### 管理后台功能

- 查看后台总览信息
- 审核帖子
- 管理评论可见性
- 切换用户是否为管理员
- 查看审计日志

### 推荐功能

- 记录阅读、点赞、收藏、分享等行为
- 导出交互数据到 CSV
- 执行离线训练
- 在线接口返回个性化推荐结果
- 模型异常时回退为热门内容

## 4. 数据与推荐链路

项目的推荐闭环如下：

1. 用户在前端浏览或互动。
2. 后端记录行为到 `PostInteraction`。
3. 训练命令从数据库导出 `daily_interactions.csv`。
4. ALS 模型训练完成后生成模型文件。
5. 推荐接口读取模型结果并返回帖子列表。
6. 当模型缺失或出错时，系统自动回退到热门排序。

当前已纳入推荐信号的行为包括：

- `read`
- `like`
- `favorite`
- `share`

## 5. 目录说明

### 根目录

- `README.md`：GitHub 首页说明
- `requirements.txt`：根 Python 依赖
- `run_project.sh`：一键启动脚本
- `.env.example`：环境变量模板
- `docs/`：项目文档目录

### 后端关键目录

- `backend_django/backend_django/`：Django 配置
- `backend_django/community/models.py`：数据模型
- `backend_django/community/views.py`：业务接口
- `backend_django/community/recommendation.py`：在线推荐逻辑
- `backend_django/community/recsys_pipeline.py`：推荐训练管道
- `backend_django/community/management/commands/`：训练与演示数据命令

### 前端关键目录

- `frontend_vue/src/api/`：接口请求封装
- `frontend_vue/src/components/`：页面和组件
- `frontend_vue/src/composables/`：状态逻辑和业务组合函数

### 推荐系统关键目录

- `recommend_system/recommender.py`：训练入口
- `recommend_system/recsys/data.py`：数据处理
- `recommend_system/recsys/trainer.py`：模型训练与评估

## 6. 第三方如何快速运行

对于第三方用户，建议按照以下最短路径运行：

```bash
git clone <your-repo-url>
cd tip
cp .env.example .env
bash run_project.sh --install
```

如果需要演示数据：

```bash
cd backend_django
python manage.py seed_demo_data
```

## 7. 当前仓库的公开化处理

为了让项目适合上传到 GitHub，当前仓库已经完成以下整理：

- 移除了本机绝对路径依赖
- `.env` 改为外部配置
- 启动命令改为第三方可执行方式
- 忽略日志、数据库、缓存和模型产物
- 补充 GitHub README 与使用文档
- 增加 GitHub Actions 自动校验

## 8. 当前确认结果

截至目前，已经确认：

- 后端测试通过
- 前端构建通过
- 文档覆盖克隆、运行、开发、上传 GitHub 全流程
- Git 跟踪内容中没有新增不该公开的运行产物

## 9. 后续可继续增强的方向

- 增加 Docker / docker-compose 部署
- 将 SQLite 切换为 PostgreSQL
- 为 README 替换为真实截图
- 增加前端 E2E 测试
- 增加线上部署说明