#!/bin/bash
set -e

APP_NAME="fashiye"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 自动检测项目根目录（scripts/ 的上一级）
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="/var/log/fashiye"
PID_DIR="/var/run/fashiye"

echo "=========================================="
echo "  $APP_NAME 一键部署脚本（就地模式）"
echo "  项目目录: $APP_DIR"
echo "=========================================="

# 检查 root
if [ "$EUID" -ne 0 ]; then
    echo "请使用 root 用户运行此脚本"
    exit 1
fi

# ---- 1. 安装系统依赖 ----
echo ""
echo "[1/7] 安装系统依赖..."
apt-get update 
apt-get install -y  python3 python3-pip python3-venv nginx certbot python3-certbot-nginx || true

# ---- 2. 创建日志/PID/备份目录 ----
echo ""
echo "[2/7] 创建日志目录..."
mkdir -p "$LOG_DIR" "$PID_DIR" "/var/backups/$APP_NAME"

# ---- 3. 创建软链接（兼容脚本中的 /opt/fashiye 引用） ----
echo ""
echo "[3/7] 创建软链接..."
if [ ! -L /opt/fashiye ] && [ ! -d /opt/fashiye ]; then
    ln -sf "$APP_DIR" /opt/fashiye
    echo "  /opt/fashiye → $APP_DIR"
elif [ -L /opt/fashiye ]; then
    rm -f /opt/fashiye
    ln -sf "$APP_DIR" /opt/fashiye
    echo "  /opt/fashiye 已更新指向"
fi

# ---- 4. 在项目内创建 venv 并安装依赖 ----
echo ""
echo "[4/7] 安装 Python 依赖（虚拟环境）..."
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --no-cache-dir -r requirements.txt -q
echo "  Python 依赖安装完成 ✓"
echo "  虚拟环境: $APP_DIR/venv"

# ---- 5. 验证数据库连接 ----
echo ""
echo "[5/7] 验证数据库连接..."
source "$APP_DIR/venv/bin/activate"
cd "$APP_DIR"
python3 -c "
from app.core.config import settings
import re

url = settings.DATABASE_URL
match = re.search(r'://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', url)
if match:
    user, pwd, host, port, db = match.groups()
    print(f'数据库: {host}:{port}/{db}')
    print(f'用户:   {user}')

try:
    import asyncio, aiomysql
    async def check():
        conn = await aiomysql.connect(
            host=host, port=int(port),
            user=user, password=pwd, db=db,
            connect_timeout=5
        )
        cur = await conn.cursor()
        await cur.execute('SELECT 1')
        await cur.close()
        conn.close()
        print('连接成功 ✓')
    asyncio.run(check())
except Exception as e:
    print(f'连接失败: {e}')
    print('⚠️ 请检查 .env 中的 DATABASE_URL 配置')
    exit(1)
" || exit 1

# ---- 6. 同步数据库表结构 ----
echo ""
echo "[6/7] 同步数据库表结构..."
source "$APP_DIR/venv/bin/activate"
cd "$APP_DIR"

TABLE_COUNT=$(python3 -c "
import asyncio, aiomysql
from app.core.config import settings
import re
match = re.search(r'://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', settings.DATABASE_URL)
user, pwd, host, port, db = match.groups()
async def check():
    conn = await aiomysql.connect(host=host, port=int(port), user=user, password=pwd, db=db, connect_timeout=5)
    cur = await conn.cursor()
    await cur.execute('SHOW TABLES')
    rows = await cur.fetchall()
    await cur.close()
    conn.close()
    print(len(rows))
asyncio.run(check())
" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "  检测到已有 $TABLE_COUNT 张表，跳过全量建表"
    python3 -c "
import asyncio, aiomysql
from app.core.config import settings
import re
match = re.search(r'://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)', settings.DATABASE_URL)
user, pwd, host, port, db = match.groups()
async def migrate():
    conn = await aiomysql.connect(host=host, port=int(port), user=user, password=pwd, db=db, connect_timeout=5)
    cur = await conn.cursor()
    await cur.execute(\"SHOW COLUMNS FROM projects LIKE 'is_single_per_order'\")
    if not await cur.fetchone():
        await cur.execute(\"ALTER TABLE projects ADD COLUMN is_single_per_order smallint DEFAULT 0 COMMENT '每单限购一个'\")
        print('✓ 添加 is_single_per_order 字段')
    await conn.commit()
    await cur.close()
    conn.close()
    print('数据库迁移完成 ✓')
asyncio.run(migrate())
" 2>/dev/null || echo "  迁移跳过，可以后续手动处理"
else
    echo "  空数据库，自动创建所有表..."
    python3 -c "
from app.models import Base
from app.db.session import engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✓ 所有表已创建')
asyncio.run(init())
" || echo "⚠️ 建表失败，请手动检查"
fi

# ---- 7. 配置 systemd 服务 ----
echo ""
echo "[7/7] 配置 systemd 服务..."
# 把 service 文件里的路径替换成实际项目目录
sed "s|/opt/fashiye|$APP_DIR|g" "$SCRIPT_DIR/fashiye.service" > "/etc/systemd/system/fashiye.service"
systemctl daemon-reload
systemctl enable fashiye
systemctl restart fashiye

sleep 3
if systemctl is-active --quiet fashiye; then
    echo "  后端服务: 运行中 ✓"
else
    echo "  ❌ 后端服务启动失败，查看日志:"
    echo "    journalctl -u fashiye -n 50 --no-pager"
fi

# ---- 可选: Nginx ----
if [ -f "$SCRIPT_DIR/nginx.conf" ]; then
    echo ""
    echo "是否配置 Nginx? (y/N): "
    read -r DO_NGINX
    if [ "$DO_NGINX" = "y" ] || [ "$DO_NGINX" = "Y" ]; then
        # 替换路径和域名占位符
        sed "s|/opt/fashiye|$APP_DIR|g" "$SCRIPT_DIR/nginx.conf" > "/etc/nginx/sites-available/$APP_NAME"
        ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/$APP_NAME"

        echo "请输入域名（留空使用IP）:"
        read -r DOMAIN
        if [ -n "$DOMAIN" ]; then
            sed -i "s/your-domain.com/$DOMAIN/g" "/etc/nginx/sites-available/$APP_NAME"
        else
            # 无域名时改 listen 为 80 不加 SSL
            sed -i 's/listen 443 ssl http2;/# 无域名，跳过 SSL/g' "/etc/nginx/sites-available/$APP_NAME"
            sed -i '/server_name.*com/d' "/etc/nginx/sites-available/$APP_NAME"
            # 只保留第一个 server block，移除 HTTPS 的 server block
            sed -i '/return 301 https/,/^}$/d' "/etc/nginx/sites-available/$APP_NAME"
        fi

        rm -f /etc/nginx/sites-enabled/default
        nginx -t && systemctl reload nginx
        echo "  Nginx 配置已应用 ✓"
    fi
fi

# ---- 完成 ----
echo ""
echo "=========================================="
echo "  $APP_NAME 部署完成!"
echo "=========================================="
echo ""
echo "项目目录: $APP_DIR"
echo "虚拟环境: $APP_DIR/venv"
echo "访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '你的服务器IP')"
echo "管理后台: /admin/login"
echo ""
echo "常用命令:"
echo "  systemctl status fashiye           # 查看服务状态"
echo "  systemctl restart fashiye          # 重启服务"
echo "  journalctl -u fashiye -f           # 实时日志"
echo "  bash $APP_DIR/scripts/logs.sh -f   # 跟踪应用日志"
echo "  bash $APP_DIR/scripts/backup.sh    # 备份数据库"
echo ""
