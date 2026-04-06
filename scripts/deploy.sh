#!/bin/bash

APP_NAME="fashiye"
APP_DIR="/opt/fashiye"
LOG_DIR="/var/log/fashiye"
PID_DIR="/var/run/fashiye"

echo "=========================================="
echo "  $APP_NAME 部署脚本"
echo "=========================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root用户运行此脚本"
    exit 1
fi

# 创建必要的目录
echo "创建目录..."
mkdir -p $APP_DIR
mkdir -p $LOG_DIR
mkdir -p $PID_DIR
mkdir -p $APP_DIR/frontend/dist

# 复制项目文件
echo "复制项目文件..."
cp -r app $APP_DIR/
cp -r alembic $APP_DIR/
cp requirements.txt $APP_DIR/
cp alembic.ini $APP_DIR/
cp .env $APP_DIR/
cp init_db.py $APP_DIR/
cp seed_games.py $APP_DIR/
cp create_admin.py $APP_DIR/

# 复制前端构建文件
echo "复制前端构建文件..."
if [ -d "frontend/dist" ]; then
    cp -r frontend/dist/* $APP_DIR/frontend/dist/
else
    echo "警告: 前端构建文件不存在，请先运行 'cd frontend && npm run build'"
fi

# 设置权限
echo "设置权限..."
chmod +x $APP_DIR/*.sh 2>/dev/null
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data $LOG_DIR
chown -R www-data:www-data $PID_DIR

# 安装Python依赖
echo "安装Python依赖..."
cd $APP_DIR
python3 -m pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python3 init_db.py

# 填充游戏数据
echo "填充游戏数据..."
python3 seed_games.py

# 创建管理员账户
echo "创建管理员账户..."
python3 create_admin.py

# 安装systemd服务
echo "安装systemd服务..."
cp scripts/fashiye.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable fashiye

# 安装Nginx配置
echo "安装Nginx配置..."
if [ -d "/etc/nginx/sites-available" ]; then
    cp scripts/nginx.conf /etc/nginx/sites-available/fashiye
    ln -sf /etc/nginx/sites-available/fashiye /etc/nginx/sites-enabled/fashiye
    nginx -t && systemctl reload nginx
fi

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "启动服务: systemctl start fashiye"
echo "停止服务: systemctl stop fashiye"
echo "重启服务: systemctl restart fashiye"
echo "查看状态: systemctl status fashiye"
echo ""
