# TIP 图文社区项目

TIP 是一个基于 Vue 3 + Django 的图文社区系统，包含社区首页、帖子发布与编辑、评论互动、个人中心、后台管理，以及基于 ALS 的个性化推荐训练链路。

## 亮点展示

### 社区业务完整

- 覆盖注册、登录、发帖、编辑、评论、点赞、收藏、关注、分享
- 适合直接展示完整的内容社区主链路

### 后台治理可演示

- 支持帖子审核、评论管理、用户管理员权限切换、审计日志
- 适合课程答辩和项目展示时演示管理能力

### 推荐系统有工程闭环

- 支持行为采集、交互导出、离线训练、在线推荐、异常回退
- 不是只停留在算法脚本，而是与业务系统完成联动

### 对第三方更友好

- 根目录环境变量模板已提供
- 一键启动脚本已提供
- CI 已覆盖后端测试和前端构建

## 项目能力

- 社区功能：注册、登录、发帖、编辑、评论、点赞、收藏、关注、分享
- 管理后台：帖子审核、评论管理、用户管理员权限切换、审计日志
- 推荐系统：行为采集、交互导出、离线训练、在线推荐、异常回退
- 开发友好：根目录环境配置、一键启动脚本、GitHub Actions CI

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus
- 后端：Django 5、SQLite、Session 认证
- 推荐：NumPy、Pandas、SciPy、scikit-learn、implicit、Optuna

## 仓库结构

```text
tip/
├── backend_django/        # Django 后端
├── frontend_vue/          # Vue 前端
├── recommend_system/      # 推荐训练与模型推理
├── docs/                  # GitHub 项目文档
├── requirements.txt       # 根 Python 依赖
├── run_project.sh         # 一键启动脚本
├── .env.example           # 环境变量模板
└── .github/workflows/     # CI 配置
```

## 第三方快速开始

```bash
git clone <your-repo-url>
cd tip
cp .env.example .env
bash run_project.sh --install
```

默认访问地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000

## 文档导航

- [项目概览](docs/PROJECT_OVERVIEW.md)
- [详细项目说明](docs/PROJECT_DETAILS.md)
- [快速开始](docs/QUICK_START.md)
- [开发与运行说明](docs/DEVELOPMENT_GUIDE.md)

## 运行前提

- Python 3.11
- Node.js 20+
- npm 10+
