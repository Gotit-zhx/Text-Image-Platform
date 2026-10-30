# 快速开始

## 环境要求

- Python 3.11
- Node.js 20.19+（或 22.12+）
- npm 10+

## 1. 克隆仓库

```bash
git clone https://github.com/Gotit-zhx/Text-Image-Platform.git
cd Text-Image-Platform
```

## 2. 配置环境变量

```bash
python3.11 -m venv .venv
source .venv/bin/activate
cp .env.example .env
```

如果你只是在本地运行，默认配置通常无需修改。

## 3. 一键安装并启动

```bash
bash run_project.sh --install
```

默认启动地址：

- 前端：http://127.0.0.1:5173
- 后端：http://127.0.0.1:8000

## 4. 手动启动方式

### 后端

```bash
cd backend_django
source ../.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### 前端

```bash
cd frontend_vue
npm ci
npm run dev
```

## 5. 初始化演示数据

如果你希望本地打开后就能看到示例内容，可以执行：

```bash
cd backend_django
../.venv/bin/python manage.py seed_demo_data
```

说明：

- 会生成 9 位创作者、12 篇图文帖子，以及评论、点赞、收藏和关注关系
- 演示图片来自 `demo_assets/` 中的公开 CC0 素材，来源与许可见 [`docs/demo-media-sources.md`](demo-media-sources.md)
- 普通导入不会新增相同帖子或重置已有账号密码；仅在明确需要重建时添加 `--reset`，该选项会清理演示账号及其内容，保留 staff/superuser
- 新建本地演示账号密码为 `DemoGarden!2026`；生产模式强制禁用示例账号密码登录，不要用示例账号承载真实数据

## 6. 创建后台管理员

```bash
cd backend_django
python manage.py createsuperuser
```

如果只需要把某个普通用户设成管理员，也可以登录后台后在“用户管理”中切换。

## 7. 运行测试与构建

### 后端测试

```bash
cd backend_django
python manage.py test
```

### 前端构建

```bash
cd frontend_vue
npm run build
```
