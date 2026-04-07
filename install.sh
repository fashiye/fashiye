#!/bin/bash

set -e

echo "============================================================"
echo "   Fashiye 一键部署脚本"
echo "============================================================"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root用户运行此脚本: sudo bash install.sh"
    exit 1
fi

# 配置变量
APP_DIR="/opt/fashiye"
LOG_DIR="/var/log/fashiye"
PID_DIR="/var/run/fashiye"
BACKUP_DIR="/var/backups/fashiye"
GITHUB_REPO="https://github.com/fashiye/fashiye.git"

# 数据库配置 (从当前.env读取)
DB_HOST="154.9.253.155"
DB_PORT="3306"
DB_NAME="dailiang_01"
DB_USER="dailiang_01"
DB_PASS="M3me6PjTAxfhRC4z"

# 安全配置
SECRET_KEY="fashiye-secret-key-$(date +%s | sha256sum | base64 | head -c 32)"
AES_SECRET_KEY="$(openssl rand -base64 32 | head -c 32)"
AES_IV="$(openssl rand -base64 16 | head -c 16)"

# 邮件配置
SMTP_HOST="smtp.163.com"
SMTP_PORT="465"
SMTP_USER="15040667931@163.com"
SMTP_PASS="GEwMY39pLSDTDEvp"

echo "[1/10] 安装系统依赖..."
apt update
apt install -y python3 python3-pip python3-venv nginx git curl

echo "[2/10] 创建目录..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
mkdir -p $PID_DIR
mkdir -p $BACKUP_DIR

echo "[3/10] 克隆代码..."
if [ -d "$APP_DIR/.git" ]; then
    echo "代码已存在，拉取最新版本..."
    cd $APP_DIR
    git pull
else
    echo "克隆仓库..."
    rm -rf $APP_DIR/*
    git clone $GITHUB_REPO $APP_DIR
    cd $APP_DIR
fi

echo "[4/10] 创建环境配置..."
cat > $APP_DIR/.env << EOF
PROJECT_NAME=Game Boost Platform
VERSION=1.0.0
DEBUG=False

SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DATABASE_URL=mysql+aiomysql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME?charset=utf8mb4

AES_SECRET_KEY=$AES_SECRET_KEY
AES_IV=$AES_IV

REDIS_URL=redis://localhost:6379/0

SMTP_HOST=$SMTP_HOST
SMTP_PORT=$SMTP_PORT
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASS
SMTP_FROM=$SMTP_USER
EOF

echo "[5/10] 安装Python依赖..."
# 直接使用系统pip，添加--break-system-packages标志，并忽略root用户警告
echo "安装Python依赖..."
python3 -m pip install --upgrade pip --break-system-packages --root-user-action=ignore
python3 -m pip install -r "$APP_DIR/requirements.txt" --break-system-packages --root-user-action=ignore

echo "[6/10] 安装Node.js..."
if ! command -v node &> /dev/null || [ "$(node -v | sed 's/v//')" -lt "20" ]; then
    echo "安装Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
fi
# 升级npm
npm install -g npm@latest

echo "[7/10] 构建前端..."
cd $APP_DIR/frontend
npm install
npm run build
cd $APP_DIR

echo "[8/10] 配置Nginx..."
# 配置为使用端口8080，避免与宝塔面板冲突
cat > /etc/nginx/sites-available/fashiye << 'NGINX_CONF'
upstream fashiye_backend {
    server 127.0.0.1:8888;
    keepalive 32;
}

server {
    listen 8080;
    server_name _;

    # 前端静态文件
    location / {
        root /opt/fashiye/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://fashiye_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /opt/fashiye/frontend/dist;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;
}
NGINX_CONF

# 移除默认站点
rm -f /etc/nginx/sites-enabled/default || true

# 创建符号链接
if [ ! -f "/etc/nginx/sites-enabled/fashiye" ]; then
    ln -s /etc/nginx/sites-available/fashiye /etc/nginx/sites-enabled/fashiye
fi

# 测试配置
nginx -t 2>/dev/null || echo "Nginx配置测试完成"

# 注意：不重启Nginx，由宝塔面板管理
echo "注意：Nginx配置已更新，请在宝塔面板中重启Nginx或重载配置"

echo "[9/10] 安装Systemd服务..."
cat > /etc/systemd/system/fashiye.service << EOF
[Unit]
Description=Fashiye Game Boosting Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8888
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$APP_DIR
StandardOutput=append:$LOG_DIR/stdout.log
StandardError=append:$LOG_DIR/stderr.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable fashiye

echo "[10/10] 启动服务..."
systemctl start fashiye

echo ""
echo "============================================================"
echo "   部署完成!"
echo "============================================================"
echo ""
echo "访问地址: http://服务器IP:8080"
echo ""
echo "管理命令:"
echo "  启动服务: systemctl start fashiye"
echo "  停止服务: systemctl stop fashiye"
echo "  重启服务: systemctl restart fashiye"
echo "  查看状态: systemctl status fashiye"
echo "  查看日志: tail -f $LOG_DIR/stdout.log"
echo ""
echo "数据库连接: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "注意：请在宝塔面板中重启Nginx或重载配置，以启用8080端口的站点"
echo ""
