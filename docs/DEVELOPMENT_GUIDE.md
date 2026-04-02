# 开发与运行说明

## 环境变量

项目根目录 `.env` 支持以下变量：

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

说明：

- `run_project.sh` 会自动加载根目录 `.env`
- Django 启动时也会读取根目录 `.env`
- 本地开发建议保留 `VITE_API_BASE_URL=/api`，通过 Vite 代理转发到 Django

## 一键启动脚本说明

```bash
bash run_project.sh --install
```

可选参数：

- `--install`：自动安装前后端依赖
- `--force`：清理占用端口的旧进程再启动

## 推荐系统训练

### 执行训练

```bash
cd backend_django
python manage.py train_recsys --trials 10 --val-ratio 0.1 --min-rows 10
```

### 仅导出交互数据

```bash
cd backend_django
python manage.py train_recsys --export-only
```

### 训练产物

- `recommend_system/cache/daily_interactions.csv`
- `recommend_system/cache/trained_model.npz`
- `backend_django/recsys_train_status.json`

## 常见问题

### 1. `python3` 找不到

设置环境变量后再运行：

```bash
PYTHON_BIN=/your/python/path bash run_project.sh --install
```

### 2. 前端能打开但接口请求失败

通常是后端没启动，或后端端口不是 `8000`。如果改了端口，请同步修改 `.env` 中的：

- `BACKEND_PORT`
- `VITE_API_BASE_URL`

### 3. 推荐内容没有变化

先执行：

```bash
cd backend_django
python manage.py train_recsys --trials 10 --val-ratio 0.1 --min-rows 1
```

然后重新访问推荐页面。


## CI 说明

GitHub Actions 已配置在 `.github/workflows/ci.yml`，默认执行：

1. 安装后端依赖
2. Django migrate
3. Django test
4. 安装前端依赖
5. 前端 build