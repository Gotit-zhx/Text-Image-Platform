# 快速开始

## 环境要求

- Python 3.11
- Node.js 20+
- npm 10+

## 1. 克隆仓库

```bash
git clone <your-repo-url>
cd tip
```

## 2. 配置环境变量

```bash
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
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

### 前端

```bash
cd frontend_vue
npm install
npm run dev
```

## 5. 初始化演示数据

如果你希望本地打开后就能看到示例内容，可以执行：

```bash
cd backend_django
python manage.py seed_demo_data
```

说明：

- 会生成 13 个示例用户
- 默认密码为 `123456`

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