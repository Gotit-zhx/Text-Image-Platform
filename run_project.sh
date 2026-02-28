#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend_django"
FRONTEND_DIR="$ROOT_DIR/frontend_vue"
LOG_DIR="$ROOT_DIR/.run_logs"

PYTHON_BIN="${PYTHON_BIN:-/home/zhx/miniconda3/envs/tip/bin/python}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

AUTO_INSTALL=0
FORCE_KILL=0
for arg in "$@"; do
  case "$arg" in
    --install)
      AUTO_INSTALL=1
      ;;
    --force)
      FORCE_KILL=1
      ;;
    *)
      echo "未知参数: $arg"
      echo "用法: ./run_project.sh [--install] [--force]"
      exit 1
      ;;
  esac
done

mkdir -p "$LOG_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python 不可执行: $PYTHON_BIN"
  echo "请设置环境变量 PYTHON_BIN，例如:"
  echo "  PYTHON_BIN=/home/zhx/miniconda3/envs/tip/bin/python ./run_project.sh"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "未找到 npm，请先安装 Node.js 和 npm"
  exit 1
fi

if [[ "$AUTO_INSTALL" -eq 1 ]]; then
  echo "[1/4] 安装后端依赖..."
  (cd "$BACKEND_DIR" && "$PYTHON_BIN" -m pip install -r requirements.txt)

  echo "[2/4] 安装前端依赖..."
  (cd "$FRONTEND_DIR" && npm install)
else
  echo "跳过依赖安装（如需安装请使用 --install）"
fi

echo "[3/4] 执行后端迁移..."
(cd "$BACKEND_DIR" && "$PYTHON_BIN" manage.py migrate)

BACKEND_PATTERN="manage.py runserver $BACKEND_HOST:$BACKEND_PORT"
FRONTEND_PATTERN="vite --host $FRONTEND_HOST --port $FRONTEND_PORT"

ensure_process_slot() {
  local pattern="$1"
  local name="$2"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  if [[ "$FORCE_KILL" -eq 1 ]]; then
    echo "检测到$name 已在运行，正在停止旧进程..."
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill "$pid" >/dev/null 2>&1 || true
    done <<< "$pids"
    sleep 1
    return 0
  fi

  echo "检测到$name 已在运行，可能导致端口占用。"
  echo "请先停止旧进程，或使用 --force 自动清理后再启动。"
  echo "匹配模式: $pattern"
  exit 1
}

ensure_process_slot "$BACKEND_PATTERN" "后端"
ensure_process_slot "$FRONTEND_PATTERN" "前端"

cleanup() {
  set +e
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    kill "$FRONTEND_PID" >/dev/null 2>&1
  fi
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1
  fi
}
trap cleanup EXIT INT TERM

echo "[4/4] 启动后端与前端..."
(
  cd "$BACKEND_DIR"
  "$PYTHON_BIN" manage.py runserver "$BACKEND_HOST:$BACKEND_PORT" --noreload
) >"$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

sleep 2
if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
  echo "后端启动失败，请查看日志: $LOG_DIR/backend.log"
  exit 1
fi

(
  cd "$FRONTEND_DIR"
  npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) >"$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

sleep 2
if ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
  echo "前端启动失败，请查看日志: $LOG_DIR/frontend.log"
  exit 1
fi

echo "项目已启动："
echo "- 后端: http://$BACKEND_HOST:$BACKEND_PORT"
echo "- 前端: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "日志文件："
echo "- $LOG_DIR/backend.log"
echo "- $LOG_DIR/frontend.log"
echo "按 Ctrl+C 可同时停止前后端。"

wait "$BACKEND_PID" "$FRONTEND_PID"
