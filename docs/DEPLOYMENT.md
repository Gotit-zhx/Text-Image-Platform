# Docker Compose 部署

本方案面向个人演示站：Caddy 提供 Vue 页面、同源 API 反向代理和自动 HTTPS，Gunicorn 运行 Django；SQLite、媒体和证书使用独立持久卷。推荐训练不在 Web 镜像中运行。Compose 默认仅监听本机回环地址，需完成云端配置后再对外开放。

## 1. 本机验证

需要 Docker Engine 与 Docker Compose v2；从项目根目录执行：

```bash
sh scripts/init-compose.sh
docker compose --env-file .env.compose up -d --build --wait --wait-timeout 120
docker compose --env-file .env.compose ps
curl --fail http://localhost:8080/healthz
```

打开 `http://localhost:8080`。此环境与原有开发数据库、媒体和 `.env` 分离；不会自动导入或清除任何业务数据。启动时执行数据库迁移、静态文件收集和部署检查；检查失败会阻止应用启动。

可选展示内容导入：

```bash
docker compose --env-file .env.compose exec app python manage.py seed_demo_data --disable-login
```

该命令导入仓库中的公开许可图片与虚构社区内容，重复执行不会新增相同帖子。生产模式始终禁用示例账号密码登录，且禁止 `seed_acceptance_data` 固定密码验收数据。不要在有实际内容的站点使用 `--reset`；图片来源见 [素材说明](demo-media-sources.md)。

创建自己的管理员账号（在终端交互输入密码）：

```bash
docker compose --env-file .env.compose exec app python manage.py createsuperuser
```

社区管理界面为 `/admin/login`；生产同源部署的 Django 原生后台为 `/django-admin/`，避免与 Vue 的 `/admin/*` 页面和刷新路由冲突。开发模式直连 Django 时仍为 `/admin/`。不要把账号密码写入 README、命令行参数或提交记录。

## 2. 云服务器与 HTTPS

1. 安装 Docker Engine 与 Compose v2，克隆仓库；无需在服务器宿主机安装项目的 Node 或 Python 依赖。
2. 为站点配置域名 A 记录；如配置 AAAA 记录，应保证对应 IPv6 也能访问该服务器。
3. 云安全组与服务器防火墙允许 TCP 80/443。SSH 限制到自己的管理来源，不开放 Django 8000 端口。
4. 执行初始化脚本，编辑 `.env.compose`，替换为自己的域名：

```dotenv
PUBLIC_ORIGIN=https://demo.example.com
DJANGO_ALLOWED_HOSTS=demo.example.com,localhost
SITE_ADDRESS=demo.example.com
UPSTREAM_SCHEME=https
BIND_ADDRESS=0.0.0.0
HTTP_PORT=80
HTTPS_PORT=443
TIP_ALLOW_REGISTRATION=false
```

`localhost` 用于内部健康检查。Caddy 需要可用 DNS、80/443 入站及证书服务出站连接。首次启动后检查证书申请日志和健康状态：

```bash
docker compose --env-file .env.compose up -d --build --wait --wait-timeout 120
docker compose --env-file .env.compose logs --tail 100 app web
curl --fail https://demo.example.com/healthz
curl --fail https://demo.example.com/api/auth/config
```

HTTPS 配置启用 Secure Cookie、HTTPS 重定向及 HSTS。`UPSTREAM_SCHEME=https` 用于明确告诉内层 Caddy 当前是公网 HTTPS 部署，避免上游代理未传递协议头时形成重定向循环。生产配置拒绝 DEBUG、明显弱密钥、通配 hosts、公网 HTTP 和无 SMTP 的开放注册。不要通过关闭这些检查解决部署错误，也不要直接公开 app 容器端口。

生产密码保存在 `.secrets/` 文件中；初始化脚本会生成 Django 密钥，重复执行不会覆盖。目录权限为 `700`；文件为 `444`，使 Linux Compose 的文件挂载可由非 root 容器用户读取。不要放宽目录权限，不要提交或展示文件内容。

## 3. 注册、邮箱和找回密码

默认关闭注册和邮件入口；浏览者可查看公开内容，登录账号由管理员提供。关闭操作同时由 API 强制执行，前端读取 `/api/auth/config` 显示可用入口。

要开放注册，先在 `.env.compose` 配置真实 SMTP：

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-mail-account
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=garden@example.com
TIP_ALLOW_REGISTRATION=true
```

将 SMTP 密码写入 `.secrets/smtp_password`，保留原权限，不要把密码放进示例环境文件。465 端口常使用 SSL，TLS/SSL 不能同时开启；具体设置以邮件服务商要求为准。修改后重建容器使文件挂载与配置生效：

```bash
docker compose --env-file .env.compose up -d --force-recreate --wait
```

必须用自己的隔离测试邮箱实际走完注册、邮件送达、验证、找回、令牌过期/重复使用流程，再对外宣称邮件能力可用。SMTP 配置通过启动检查不等于邮件已经送达。没有 SMTP 时，保持关闭策略；file/console 邮件仅供本地验证。

## 4. 备份与恢复

数据库和媒体分别位于 `database`、`media` 卷；Caddy 的 `caddy_data` 卷保存证书。重建镜像不会清理这些卷。**不要执行 `docker compose down -v` 或 `docker volume prune` 来更新站点。**

执行一致性备份：

```bash
sh scripts/backup-compose.sh
docker compose --env-file .env.compose ps
```

脚本短暂停止 app，使用 SQLite backup API 并检查数据库完整性，再将数据库和媒体写入 `backups/*.tar.gz`，结束后恢复原本运行的 app。期间页面可能出现 API 暂不可用，适合低访问量时执行。脚本拒绝覆盖已有备份；失败时删除不完整归档并尝试重新启动 app。可传入自定义归档路径，通过 `COMPOSE_ENV_FILE` 指定配置文件，通过 `COMPOSE_PROJECT_NAME` 选择栈。

把归档复制到服务器之外，并单独加密备份 `.secrets/` 与 `.env.compose`。归档可能包含私人内容和账号数据，不得上传公开仓库。仅保留服务器本地副本不构成异机备份。

优先在新的隔离 Compose 项目恢复并验证，以下命令针对全新、无业务数据的 `baicaoyuan-restore` 项目：

```bash
# 解压到权限受限的本地暂存目录；只使用自己可信来源的备份。
mkdir -p backups/restore
chmod 700 backups/restore
tar -xzf backups/baicaoyuan-YYYYMMDDTHHMMSSZ.tar.gz -C backups/restore

# 新项目的卷是独立的；run 不发布站点端口。
docker compose --env-file .env.compose -p baicaoyuan-restore run --build --rm --no-deps -T \
  -v "$PWD/backups/restore:/restore:ro" app python -c '
import shutil
from pathlib import Path
db = Path("/data/db.sqlite3")
media = Path("/media")
if db.exists() or any(media.iterdir()):
    raise SystemExit("Restore target must be empty; no data was changed.")
shutil.copy2("/restore/db.sqlite3", db)
shutil.copytree("/restore/media", media, dirs_exist_ok=True)
'

# 在隔离项目内检查迁移和数据库，不访问原站点数据。
docker compose --env-file .env.compose -p baicaoyuan-restore run --rm --no-deps -T app python manage.py migrate --check
docker compose --env-file .env.compose -p baicaoyuan-restore run --rm --no-deps -T app python manage.py check
```

恢复后核对帖子/账号数量和媒体读取，按需要为隔离站点配置不同端口或域名再启动 web。生产卷覆盖恢复有数据丢失风险，应先保留当前完整备份并停写，再由维护者确认目标卷与恢复时间点。

## 5. 更新与回滚

更新前备份，并记录 `git rev-parse HEAD` 与当前镜像 ID；保留可回滚的旧镜像和备份：

```bash
git pull --ff-only
docker compose --env-file .env.compose up -d --build --wait --wait-timeout 120
docker compose --env-file .env.compose logs --tail 100 app web
```

启动脚本会迁移数据库。代码回滚不等于数据库回滚：若迁移不兼容旧代码，必须同时恢复对应数据库与媒体备份。不要在尚未确认兼容性时对生产数据库强行反向迁移。健康检查失败时先保留日志，核对配置、磁盘空间、卷权限与迁移结果。

## 6. 演示站限制与上线前检查

- SQLite 仅运行一个 app 实例、一个 Gunicorn 进程和有限线程；当前适用于个人演示，不代表高并发容量。流量扩大前迁移 PostgreSQL、共享缓存与对象存储，并执行负载测试。
- 登录/邮件频率限制使用进程内缓存，重启会重置；需结合服务器网络层限制与访问监控。暂未提供公开匿名上传能力，上传需登录并受文件尺寸、像素与资源数量限制。
- 上传图片经过服务端校验与重编码；媒体由鉴权接口提供，不能把媒体卷直接作为不鉴权静态目录公开。
- Caddy 不开启访问日志，Gunicorn 日志排除查询参数；不要把验证/重置令牌、密码、邮件文件或完整环境配置贴到公开日志中。
- 监控磁盘、数据库备份、证书续期和容器健康；Docker 日志有轮转，媒体与邮件仍需容量管理。
- 依赖版本审计、自动测试和桌面浏览器验收不能替代真实 SMTP、公网证书、实体手机软键盘/手势及辅助技术验收。未执行项应在本地检查记录中保持明确标记。

项目是演示性质的持续开发软件；上线前按实际启用的功能完成验收，关闭尚未具备外部依赖的入口。
