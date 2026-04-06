#!/bin/bash

APP_NAME="fashiye"
APP_DIR="/opt/fashiye"
LOG_DIR="/var/log/fashiye"
PID_DIR="/var/run/fashiye"
PID_FILE="$PID_DIR/backend.pid"
LOG_FILE="$LOG_DIR/backend.log"

echo "启动 $APP_NAME 服务..."

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "$APP_NAME 后端服务已经在运行 (PID: $PID)"
        exit 0
    fi
fi

# 创建必要的目录
mkdir -p $LOG_DIR
mkdir -p $PID_DIR

# 启动后端服务
cd $APP_DIR
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8888 > $LOG_FILE 2>&1 &
echo $! > $PID_FILE

echo "$APP_NAME 后端服务已启动 (PID: $(cat $PID_FILE))"
echo "日志文件: $LOG_FILE"
