#!/bin/bash
set -e

APP_NAME="fashiye"
APP_DIR="/opt/fashiye"
LOG_DIR="/var/log/fashiye"
PID_DIR="/var/run/fashiye"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "  $APP_NAME 一键部署脚本"
echo "=========================================="

# 检查 root
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 用户运行此脚本"
    exit 1
fi

# ---- 1. 安装系统依赖 ----
echo ""
echo "[1/8] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx mysql-server redis-server certbot python3-certbot-nginx || true

# ---- 2. 创建目录结构 ----
echo ""
echo "[2/8] 创建目录..."
mkdir -p "$APP_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"
mkdir -p "$APP_DIR/frontend/dist"
mkdir -p "/var/backups/$APP_NAME"

# ---- 3. 复制项目文件 ----
echo ""
echo "[3/8] 复制项目文件..."
cp -r "$SCRIPT_DIR/../app" "$APP_DIR/app"
cp -r "$SCRIPT_DIR/../alembic" "$APP_DIR/alembic"
cp -r "$SCRIPT_DIR/../frontend/dist" "$APP_DIR/frontend/dist"
cp "$SCRIPT_DIR/../requirements.txt" "$APP_DIR/"
cp "$SCRIPT_DIR/../alembic.ini" "$APP_DIR/"
cp "$SCRIPT_DIR/../.env" "$APP_DIR/" 2>/dev/null || echo "警告: .env 文件不存在，请手动创建"
cp "$SCRIPT_DIR"/*.sh "$APP_DIR/scripts/" 2>/dev/null || true
cp "$SCRIPT_DIR/fashiye.service" "/etc/systemd/system/"

# ---- 4. 创建 Python 虚拟环境并安装依赖 ----
echo ""
echo "[4/8] 安装 Python 依赖..."
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
fi
source "$APP_DIR/venv/bin/activate"
pip install --no-cache-dir -r "$APP_DIR/requirements.txt" -q

# ---- 5. 配置 MySQL ----
echo ""
echo "[5/8] 配置 MySQL..."
systemctl enable mysql
systemctl start mysql

# 从 .env 解析数据库配置
if [ -f "$APP_DIR/.env" ]; then
    DB_URL=$(grep DATABASE_URL "$APP_DIR/.env" | cut -d '=' -f2-)
    DB_NAME=$(echo "$DB_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    DB_USER=$(echo "$DB_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo "$DB_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

    mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
CREATE USER IF NOT EXISTS '$DB_USER'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'127.0.0.1';
FLUSH PRIVILEGES;
EOF
    echo "数据库 $DB_NAME 已就绪"
fi

# ---- 6. 运行数据库迁移 ----
echo ""
echo "[6/8] 运行数据库迁移..."
source "$APP_DIR/venv/bin/activate"
cd "$APP_DIR"
alembic upgrade head 2>/dev/null || echo "Alembic 迁移跳过，尝试直接同步模型..."
# 若 Alembic 不可用，自动建表
python3 -c "
from app.models import Base
from app.db.session import engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
print('数据库表结构已同步')
" || echo "警告: 数据库同步失败，请手动检查"

# ---- 7. 安装并启动 systemd 服务 ----
echo ""
echo "[7/8] 配置 systemd 服务..."
systemctl daemon-reload
systemctl enable fashiye
systemctl restart fashiye

# 等待服务启动
sleep 3
if systemctl is-active --quiet fashiye; then
    echo "后端服务: 运行中 ✓"
else
    echo "后端服务: 启动失败，查看日志: journalctl -u fashiye -n 50"
fi

# ---- 8. 配置 Nginx ----
echo ""
echo "[8/8] 配置 Nginx..."
if [ -f "$SCRIPT_DIR/nginx.conf" ]; then
    cp "$SCRIPT_DIR/nginx.conf" "/etc/nginx/sites-available/$APP_NAME"
    ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/$APP_NAME"

    # 替换域名占位符
    if [ -n "$DOMAIN" ]; then
        sed -i "s/your-domain.com/$DOMAIN/g" "/etc/nginx/sites-available/$APP_NAME"
    fi

    # 测试并重载
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    echo "Nginx 配置已应用 ✓"
fi

# ---- 完成 ----
echo ""
echo "=========================================="
echo "  $APP_NAME 部署完成!"
echo "=========================================="
echo ""
echo "访问地址: http://$(curl -s ifconfig.me || echo 'your-server-ip')"
echo "管理后台: /admin"
echo ""
echo "常用命令:"
echo "  systemctl status fashiye    # 查看服务状态"
echo "  systemctl stop fashiye      # 停止服务"
echo "  systemctl restart fashiye   # 重启服务"
echo "  journalctl -u fashiye -f    # 实时查看日志"
echo "  bash scripts/backup.sh      # 备份数据库"
echo "  bash scripts/logs.sh -f     # 跟踪应用日志"
echo ""
