# 项目概览

## 项目是什么

TIP 是一个图文社区项目，目标是把内容社区和个性化推荐放在同一个工程里完成。用户既可以完成常见社区操作，也可以通过行为数据驱动推荐结果变化。

## 主要功能

- 用户注册、登录、退出和会话恢复
- 首页信息流，支持推荐、热门、更新、关注等内容视图
- 帖子发布、编辑、富文本内容展示
- 评论、点赞、收藏、关注、分享
- 个人中心资料与内容管理
- 管理后台：帖子审核、评论管理、用户管理员权限设置、审计日志
- 推荐训练：导出交互数据并训练 ALS 模型

## 技术架构

### 前端

- Vue 3 + TypeScript
- Vite
- Element Plus

### 后端

- Django 5
- SQLite
- Session 认证

### 推荐系统

- implicit ALS
- Optuna 参数搜索
- NumPy / Pandas / SciPy / scikit-learn

## 目录说明

- `backend_django/`：后端 API、数据模型、管理接口、训练命令
- `frontend_vue/`：前端页面、组件、请求封装、状态逻辑
- `recommend_system/`：推荐训练和推理脚本
- `docs/`：GitHub 使用文档
- `run_project.sh`：一键启动前后端

## 推荐链路说明

1. 用户在页面中产生 `read`、`like`、`favorite`、`share` 等行为。
2. 后端把行为记录到 `PostInteraction`。
3. `train_recsys` 命令导出交互数据到 `recommend_system/cache/`。
4. 推荐模型训练完成后，在线推荐接口优先返回个性化内容。
5. 当模型不可用时，系统自动回退到热门内容排序。

## 适合谁使用

- 想展示全栈项目的人
- 想展示毕业设计/课程设计成果的人
- 想研究 Vue + Django 联调的人
- 想做推荐系统工程实践入门的人