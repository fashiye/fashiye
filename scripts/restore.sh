#!/bin/bash

BACKUP_DIR="/var/backups/fashiye"
ENV_FILE="/opt/fashiye/.env"

show_usage() {
    echo "用法: $0 [备份文件]"
    echo ""
    echo "可用的备份文件:"
    ls -lh $BACKUP_DIR/*.sql.gz 2>/dev/null || echo "  没有找到备份文件"
    echo ""
}

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

BACKUP_FILE=$1

# 如果没有指定完整路径，则在备份目录中查找
if [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# 如果文件不存在，尝试添加.gz后缀
if [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_FILE="${BACKUP_FILE}.gz"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 找不到备份文件: $BACKUP_FILE"
    show_usage
    exit 1
fi

# 从.env文件读取数据库配置
if [ -f "$ENV_FILE" ]; then
    DB_URL=$(grep DATABASE_URL $ENV_FILE | cut -d '=' -f2-)
    DB_USER=$(echo $DB_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DB_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo $DB_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DB_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
else
    echo "错误: 找不到.env文件"
    exit 1
fi

echo "警告: 此操作将覆盖当前数据库!"
echo "数据库: $DB_NAME"
echo "备份文件: $BACKUP_FILE"
echo ""
read -p "确认恢复? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "操作已取消"
    exit 0
fi

echo "开始恢复数据库..."

# 解压并恢复
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS $DB_NAME
else
    mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS $DB_NAME < $BACKUP_FILE
fi

if [ $? -eq 0 ]; then
    echo "数据库恢复成功!"
else
    echo "数据库恢复失败!"
    exit 1
fi
