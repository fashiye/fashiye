#!/bin/bash

APP_NAME="fashiye"
APP_DIR="/opt/fashiye"
PID_DIR="/var/run/fashiye"
PID_FILE="$PID_DIR/backend.pid"
LOG_DIR="/var/log/fashiye"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  $APP_NAME 服务状态"
echo "=========================================="

# 检查后端服务
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo -e "后端服务: ${GREEN}运行中${NC} (PID: $PID)"
        # 获取端口
        PORT=$(ss -tlnp | grep "$PID" | awk '{print $4}' | awk -F: '{print $NF}' | head -1)
        echo "  - 端口: ${PORT:-8888}"
        echo "  - 进程数: $(ps --ppid $PID -o pid= 2>/dev/null | wc -l)"
        echo "  - 内存: $(ps -o rss= -p $PID 2>/dev/null | awk '{printf "%.1f MB", $1/1024}')"
        echo "  - 运行时间: $(ps -o etime= -p $PID 2>/dev/null | xargs)"
    else
        echo -e "后端服务: ${RED}已停止${NC} (PID文件存在但进程不存在)"
        rm -f "$PID_FILE"
    fi
else
    echo -e "后端服务: ${RED}未运行${NC}"
fi

echo ""

# 检查 Nginx
if command -v nginx &>/dev/null; then
    if nginx -t 2>&1 | grep -q "syntax is ok"; then
        echo -e "Nginx: ${GREEN}配置正确${NC}"
    else
        echo -e "Nginx: ${RED}配置错误${NC}"
    fi
    if pgrep nginx >/dev/null; then
        echo "  - 状态: 运行中"
    else
        echo -e "  - 状态: ${RED}未运行${NC}"
    fi
fi

echo ""

# 检查 MySQL
if command -v mysql &>/dev/null; then
    if mysqladmin ping -u root --silent 2>/dev/null; then
        echo -e "MySQL: ${GREEN}运行中${NC}"
    else
        echo -e "MySQL: ${RED}未运行${NC}"
    fi
fi

echo ""

# 检查磁盘和日志
echo "资源使用:"
echo "  - 日志目录: $(du -sh $LOG_DIR 2>/dev/null | cut -f1 || echo 'N/A')"
echo "  - 应用目录: $(du -sh $APP_DIR 2>/dev/null | cut -f1 || echo 'N/A')"
echo "  - 磁盘剩余: $(df -h / | awk 'NR==2{print $4}')"
echo "  - 内存剩余: $(free -h | awk 'NR==2{print $7}')"

# 检查最近的错误
if [ -f "$LOG_DIR/error.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR" "$LOG_DIR/error.log" 2>/dev/null || echo 0)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "  - 错误日志: ${YELLOW}$ERROR_COUNT 条错误${NC}"
    fi
fi

echo ""
echo "日志: $LOG_DIR"
echo "PID: $PID_FILE"
echo "=========================================="
