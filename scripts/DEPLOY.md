# Fashiye 部署指南

## 系统要求

- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Python 3.9+
- MySQL 8.0+
- Nginx
- Node.js 18+ (仅构建前端时需要)

## 快速部署

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3 python3-pip mysql-server nginx

# 安装Python依赖
sudo pip3 install -r requirements.txt
```

### 2. 配置数据库

```bash
# 登录MySQL
sudo mysql -u root -p

# 创建数据库和用户
CREATE DATABASE dailiang_01 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fashiye'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dailiang_01.* TO 'fashiye'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置环境变量

```bash
# 复制并编辑.env文件
cp .env.example .env
nano .env
```

修改以下配置:
```
DATABASE_URL=mysql+aiomysql://fashiye:your_password@localhost:3306/dailiang_01
SECRET_KEY=your_secret_key_here
```

### 4. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. 运行部署脚本

```bash
# 复制脚本到服务器
scp -r scripts/ user@server:/opt/fashiye/

# 运行部署脚本
sudo bash scripts/deploy.sh
```

### 6. 启动服务

```bash
# 使用systemd
sudo systemctl start fashiye
sudo systemctl enable fashiye

# 或使用脚本
sudo bash scripts/start.sh
```

## 管理命令

### 服务管理

```bash
# 启动服务
sudo systemctl start fashiye
# 或
sudo bash scripts/start.sh

# 停止服务
sudo systemctl stop fashiye
# 或
sudo bash scripts/stop.sh

# 重启服务
sudo systemctl restart fashiye
# 或
sudo bash scripts/restart.sh

# 查看状态
sudo systemctl status fashiye
# 或
sudo bash scripts/status.sh
```

### 日志管理

```bash
# 查看最近日志
sudo bash scripts/logs.sh

# 实时跟踪日志
sudo bash scripts/logs.sh -f

# 查看错误日志
sudo bash scripts/logs.sh -e

# 查看最近500行
sudo bash scripts/logs.sh -n 500
```

### 数据库备份与恢复

```bash
# 备份数据库
sudo bash scripts/backup.sh

# 查看可用备份
sudo bash scripts/restore.sh

# 恢复数据库
sudo bash scripts/restore.sh fashiye_20240101_120000.sql.gz
```

## Nginx配置

1. 复制Nginx配置:
```bash
sudo cp scripts/nginx.conf /etc/nginx/sites-available/fashiye
sudo ln -s /etc/nginx/sites-available/fashiye /etc/nginx/sites-enabled/
```

2. 修改配置中的域名和SSL证书路径

3. 测试并重载Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## SSL证书配置

使用Let's Encrypt:

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

## 定时任务

设置定时备份:

```bash
# 编辑crontab
sudo crontab -e

# 添加每天凌晨2点备份
0 2 * * * /opt/fashiye/scripts/backup.sh >> /var/log/fashiye/backup.log 2>&1
```

## 故障排除

### 服务无法启动

1. 检查日志:
```bash
sudo bash scripts/logs.sh -e
```

2. 检查端口占用:
```bash
sudo netstat -tlnp | grep 8888
```

3. 检查数据库连接:
```bash
mysql -u fashiye -p -h localhost dailiang_01
```

### 前端页面无法访问

1. 检查Nginx状态:
```bash
sudo systemctl status nginx
```

2. 检查Nginx配置:
```bash
sudo nginx -t
```

3. 检查前端文件:
```bash
ls -la /opt/fashiye/frontend/dist/
```

## 目录结构

```
/opt/fashiye/
├── app/                 # 后端应用
├── frontend/
│   └── dist/           # 前端构建文件
├── scripts/            # 管理脚本
├── .env                # 环境变量
└── requirements.txt    # Python依赖

/var/log/fashiye/       # 日志目录
/var/run/fashiye/       # PID文件目录
/var/backups/fashiye/   # 备份目录
```
