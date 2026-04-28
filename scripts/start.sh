#!/bin/bash
set -e

APP_NAME="fashiye"
APP_DIR="/opt/fashiye"
LOG_DIR="/var/log/fashiye"
PID_DIR="/var/run/fashiye"
PID_FILE="$PID_DIR/backend.pid"
LOG_FILE="$LOG_DIR/backend.log"
ERROR_LOG="$LOG_DIR/error.log"

cd "$APP_DIR"

# 使用 gunicorn 多 worker 生产部署
GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
GUNICORN_BIND=${GUNICORN_BIND:-"0.0.0.0:8888"}

echo "启动 $APP_NAME 生产服务..."
echo "  - 监听: $GUNICORN_BIND"
echo "  - Worker: $GUNICORN_WORKERS"
echo "  - 日志: $LOG_DIR"

# 创建必要目录
mkdir -p "$LOG_DIR" "$PID_DIR"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "$APP_NAME 已在运行 (PID: $OLD_PID)"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# 使用 gunicorn + uvicorn worker 启动生产服务
exec nohup gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "$GUNICORN_WORKERS" \
    --bind "$GUNICORN_BIND" \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$ERROR_LOG" \
    --log-level info \
    --pid "$PID_FILE" \
    --daemon \
    >> "$LOG_FILE" 2>&1 &

echo "$APP_NAME 后端服务已启动"
echo "查看日志: ./scripts/logs.sh"
