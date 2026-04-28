#!/bin/bash

BACKUP_DIR="/var/backups/fashiye"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fashiye_$DATE.sql"

# 从.env文件读取数据库配置
ENV_FILE="/opt/fashiye/.env"

if [ -f "$ENV_FILE" ]; then
    # 提取数据库URL
    DB_URL=$(grep DATABASE_URL $ENV_FILE | cut -d '=' -f2-)
    
    # 解析数据库连接信息
    # 格式: mysql+aiomysql://user:password@host:port/database
    DB_USER=$(echo $DB_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DB_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo $DB_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DB_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
else
    echo "错误: 找不到.env文件"
    exit 1
fi

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "开始备份数据库..."
echo "数据库: $DB_NAME"
echo "主机: $DB_HOST:$DB_PORT"

# 执行备份
mysqldump -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS --single-transaction --routines --triggers $DB_NAME > $BACKUP_FILE

if [ $? -eq 0 ]; then
    # 压缩备份文件
    gzip $BACKUP_FILE
    
    # 删除30天前的备份
    find $BACKUP_DIR -name "fashiye_*.sql.gz" -mtime +30 -delete
    
    echo "备份完成: ${BACKUP_FILE}.gz"
    echo "备份大小: $(du -h ${BACKUP_FILE}.gz | cut -f1)"
else
    echo "备份失败!"
    rm -f $BACKUP_FILE
    exit 1
fi
