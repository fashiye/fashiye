#!/bin/bash

APP_NAME="fashiye"

echo "停止 $APP_NAME 服务..."

PID=$(pgrep -f "gunicorn.*app.main:app" | head -1)

if [ -z "$PID" ]; then
    echo "$APP_NAME 后端服务未运行"
    exit 0
fi

kill "$PID"

for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "$APP_NAME 后端服务已停止"
        exit 0
    fi
    sleep 1
done

echo "强制终止 $APP_NAME 后端服务..."
kill -9 "$PID"
echo "$APP_NAME 后端服务已强制停止"
