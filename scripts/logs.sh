#!/bin/bash

LOG_DIR="/var/log/fashiye"
LOG_FILE="$LOG_DIR/backend.log"
ERROR_LOG="$LOG_DIR/stderr.log"

show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -a, --all       显示所有日志"
    echo "  -e, --error     显示错误日志"
    echo "  -f, --follow    实时跟踪日志"
    echo "  -n NUM          显示最后NUM行日志 (默认: 100)"
    echo "  -h, --help      显示帮助信息"
    echo ""
}

LINES=100
FOLLOW=false
SHOW_ERROR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            LINES=10000
            shift
            ;;
        -e|--error)
            SHOW_ERROR=true
            shift
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n)
            LINES=$2
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_usage
            exit 1
            ;;
    esac
done

if [ ! -d "$LOG_DIR" ]; then
    echo "日志目录不存在: $LOG_DIR"
    exit 1
fi

if $SHOW_ERROR; then
    if [ -f "$ERROR_LOG" ]; then
        if $FOLLOW; then
            tail -f $ERROR_LOG
        else
            tail -n $LINES $ERROR_LOG
        fi
    else
        echo "错误日志文件不存在"
    fi
else
    if [ -f "$LOG_FILE" ]; then
        if $FOLLOW; then
            tail -f $LOG_FILE
        else
            tail -n $LINES $LOG_FILE
        fi
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
fi
