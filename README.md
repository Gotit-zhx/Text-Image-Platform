# TIP 图文社区项目

一个基于 Vue 3 + Django 的图文社区系统，包含社区首页、帖子发布与编辑、评论互动、个人中心、后台管理，以及基于 ALS 的个性化推荐训练链路。

## 项目特性

- 社区主链路完整：注册、登录、发帖、编辑、评论、点赞、收藏、关注、分享
- 管理后台完整：帖子审核、评论管理、用户管理、审计日志
- 推荐系统闭环：行为采集、数据导出、离线训练、在线推荐、异常回退
- 前后端分离：Vue 3 + Vite 前端，Django 后端 API
- 适合课程设计、毕业设计、论文演示和二次开发

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus
- 后端：Django 5、SQLite、Session 认证
- 推荐：NumPy、Pandas、SciPy、scikit-learn、implicit、Optuna

## 目录结构

```text
tip/
├── backend_django/      # Django 后端
├── frontend_vue/        # Vue 前端
├── recommend_system/    # ALS 推荐训练与推理
├── docs/                # 总体说明文档
├── requirements.txt     # 根依赖清单
├── run_project.sh       # 一键启动脚本
└── .env.example         # 环境变量模板
```

## 运行环境

- Python 3.11
- Node.js 20+
- npm 10+

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd tip
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

默认情况下，项目会从根目录 `.env` 自动读取 Django 与启动脚本所需配置。

### 3. 安装依赖并启动

推荐直接使用一键脚本：

```bash
bash run_project.sh --install
```

启动后默认地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000

### 4. 手动启动

后端：

```bash
cd backend_django
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

前端：

```bash
cd frontend_vue
npm install
npm run dev
```

本地开发时前端默认通过 Vite 代理访问 `/api`，通常无需额外配置前端接口地址。

## 初始化数据

如需演示数据，可执行：

```bash
cd backend_django
python manage.py seed_demo_data
```

如需管理后台账号，可执行：

```bash
cd backend_django
python manage.py createsuperuser
```

## 推荐系统训练

执行一次训练：

```bash
cd backend_django
python manage.py train_recsys --trials 10 --val-ratio 0.1 --min-rows 10
```

主要产物：

- `recommend_system/cache/daily_interactions.csv`
- `recommend_system/cache/trained_model.npz`
- `backend_django/recsys_train_status.json`

## 环境变量说明

根目录 `.env` 支持以下变量：

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
PYTHON_BIN=python3
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5173
VITE_API_BASE_URL=/api
```

## GitHub 上传前建议

本仓库已经加入以下忽略规则：

- `.env`
- `.run_logs/`
- `__pycache__/`
- `*.sqlite3`
- `recommend_system/cache/`
- `frontend_vue/.env`
- `node_modules/`
- `dist/`

如果这些运行产物已经被 Git 跟踪，首次公开上传前请执行：

```bash
git rm --cached -r .run_logs backend_django/__pycache__ backend_django/community/__pycache__ backend_django/community/management/commands/__pycache__ recommend_system/cache frontend_vue/dist frontend_vue/node_modules
git rm --cached backend_django/db.sqlite3 backend_django/recsys_train_status.json
```

## CI

仓库已包含 GitHub Actions 配置：

- 安装后端依赖
- 执行 Django migrate
- 运行 Django tests
- 安装前端依赖
- 执行前端构建

工作流文件位置：`.github/workflows/ci.yml`
