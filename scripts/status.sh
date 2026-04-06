#!/bin/bash

APP_NAME="fashiye"
PID_DIR="/var/run/fashiye"
PID_FILE="$PID_DIR/backend.pid"
LOG_DIR="/var/log/fashiye"

echo "=========================================="
echo "  $APP_NAME 服务状态"
echo "=========================================="

# 检查后端服务
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "后端服务: 运行中 (PID: $PID)"
        echo "  - 端口: 8888"
        echo "  - 日志: $LOG_DIR/backend.log"
    else
        echo "后端服务: 已停止 (PID文件存在但进程不存在)"
    fi
else
    echo "后端服务: 未运行"
fi

echo ""

# 检查Nginx
if command -v nginx &> /dev/null; then
    if pgrep nginx > /dev/null; then
        echo "Nginx: 运行中"
    else
        echo "Nginx: 未运行"
    fi
else
    echo "Nginx: 未安装"
fi

echo ""

# 检查MySQL
if command -v mysql &> /dev/null; then
    if pgrep mysqld > /dev/null; then
        echo "MySQL: 运行中"
    else
        echo "MySQL: 未运行"
    fi
else
    echo "MySQL: 未安装"
fi

echo ""

# 检查磁盘空间
echo "磁盘空间:"
df -h /opt/fashiye 2>/dev/null || df -h /

echo ""
echo "=========================================="
