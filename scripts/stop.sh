#!/bin/bash

APP_NAME="fashiye"
PID_DIR="/var/run/fashiye"
PID_FILE="$PID_DIR/backend.pid"

echo "停止 $APP_NAME 服务..."

# 检查是否在运行
if [ ! -f "$PID_FILE" ]; then
    echo "$APP_NAME 后端服务未运行"
    exit 0
fi

PID=$(cat $PID_FILE)

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "$APP_NAME 后端服务未运行"
    rm -f $PID_FILE
    exit 0
fi

# 发送SIGTERM信号
kill $PID

# 等待进程结束
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "$APP_NAME 后端服务已停止"
        rm -f $PID_FILE
        exit 0
    fi
    sleep 1
done

# 强制终止
echo "强制终止 $APP_NAME 后端服务..."
kill -9 $PID
rm -f $PID_FILE
echo "$APP_NAME 后端服务已强制停止"
