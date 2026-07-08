#!/bin/bash
# =============================================================================
# Fashiye 游戏代肝平台 - 服务器全自动部署脚本
# 用途：在全新 Ubuntu/Debian/CentOS 服务器上一键安装所有依赖+部署+启动
# 用法：以 root 身份执行:  bash deploy_full.sh
# =============================================================================
set -e

# 设置 UTF-8 语言环境以支持中文变量名（某些服务器 locale 默认非 UTF-8）
# 传入：LC_ALL, LANG 环境变量
# 作用：确保 bash 能够正确解析中文命名的变量（赋值和引用）
# 传出：无返回值
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# ============ 可配置参数 ============
APP_NAME="fashiye"
BAOTA_MODE=true                                       # 宝塔面板模式（使用宝塔路径和管理）
if [ "$BAOTA_MODE" = true ]; then
    APP_DIR="/www/wwwroot/fashiye"                    # 宝塔站点目录
    LOG_DIR="/www/wwwroot/fashiye/logs"               # 日志目录
    PID_DIR="/www/wwwroot/fashiye/run"                # PID目录
    BACKUP_DIR="/www/wwwroot/fashiye/backups"         # 备份目录
    MYSQL_ROOT_PASSWORD="admin"                       # 宝塔MySQL默认root密码
    BAOTA_NGINX_VHOST="/www/server/panel/vhost/nginx" # 宝塔Nginx站点配置目录
else
    APP_DIR="/opt/fashiye"                            # 项目安装目录
    LOG_DIR="/var/log/fashiye"                        # 日志目录
    PID_DIR="/var/run/fashiye"                        # PID目录
    BACKUP_DIR="/var/backups/fashiye"                 # 备份目录
    MYSQL_ROOT_PASSWORD=""                            # MySQL root密码（留空自动生成）
fi

MYSQL_APP_USER="fashiye"                              # MySQL应用用户名
MYSQL_APP_PASSWORD=""                                 # MySQL应用用户密码（留空自动生成）
MYSQL_DB_NAME="dailiang_01"                           # 数据库名

GUNICORN_WORKERS=4                                    # Gunicorn 工作进程数
GUNICORN_BIND="127.0.0.1:8888"                        # Gunicorn 监听地址（Nginx反代后端用本地）

DOMAIN=""                                             # 域名（留空用IP访问，不配置SSL）
# ====================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Fashiye 游戏代肝平台 - 全自动部署脚本 v1.0            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ---------- 0. 必须以 root 执行 ----------
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 root 用户运行此脚本 (sudo -i)"
    exit 1
fi

# ---------- 0.1 自动生成随机密码函数 ----------
生成随机密码() {
    local length="${1:-16}"
    # 传入：密码长度（默认16位）
    # 作用：使用 urandom 读取随机字节，过滤出字母数字，截取指定长度
    # 传出：随机密码字符串
    tr -dc 'A-Za-z0-9!@#$%^&*' < /dev/urandom | head -c "${length}"
}

# ---------- 0.2 检测操作系统 ----------
检测操作系统() {
    # 传入：无
    # 作用：读取 /etc/os-release 判断发行版类型，设置包管理器和包名
    # 传出：全局变量 OS_FAMILY, PKG_INSTALL, PKG_UPDATE, MYSQL_PKG
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        case "$ID" in
            ubuntu|debian|linuxmint|pop|elementary|zorin)
                OS_FAMILY="debian"
                PKG_UPDATE="apt-get update -y"
                PKG_INSTALL="apt-get install -y"
                MYSQL_PKG="mysql-server"
                NGINX_PKG="nginx"
                echo "✅ 检测到 Debian/Ubuntu 系发行版: $PRETTY_NAME"
                ;;
            centos|rhel|rocky|almalinux|fedora|ol)
                OS_FAMILY="rhel"
                PKG_UPDATE="yum update -y"
                PKG_INSTALL="yum install -y"
                MYSQL_PKG="mysql-server"
                NGINX_PKG="nginx"
                # CentOS 8+ 用 dnf
                if command -v dnf >/dev/null 2>&1; then
                    PKG_INSTALL="dnf install -y"
                    PKG_UPDATE="dnf update -y"
                fi
                echo "✅ 检测到 RHEL/CentOS 系发行版: $PRETTY_NAME"
                ;;
            *)
                echo "⚠️  未知发行版: $ID，尝试按 Debian/Ubuntu 处理"
                OS_FAMILY="debian"
                PKG_UPDATE="apt-get update -y"
                PKG_INSTALL="apt-get install -y"
                MYSQL_PKG="mysql-server"
                NGINX_PKG="nginx"
                ;;
        esac
    else
        echo "❌ 无法检测操作系统，请手动执行部署"
        exit 1
    fi
}

# ---------- 1. 安装系统依赖 ----------
步骤1_安装基础依赖() {
    echo ""
    echo "[1/9] 安装系统基础依赖..."
    echo "────────────────────────────────────────"

    # Debian/Ubuntu 先更新
    if [ "$OS_FAMILY" = "debian" ]; then
        export DEBIAN_FRONTEND=noninteractive
        $PKG_UPDATE 2>&1 | tail -5
        $PKG_INSTALL curl wget ca-certificates gnupg lsb-release software-properties-common tzdata locales 2>&1 | tail -5
    else
        $PKG_UPDATE 2>&1 | tail -5
        $PKG_INSTALL curl wget ca-certificates gnupg tzdata 2>&1 | tail -5
    fi

    # 设置时区为上海
    # 传入：时区路径
    # 作用：将系统时区符号链接指向 Asia/Shanghai
    # 传出：无返回值
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime 2>/dev/null || true
    echo "Asia/Shanghai" > /etc/timezone 2>/dev/null || true

    echo "✅ 基础依赖安装完成"
}

# ---------- 2. 安装 Python 3.10+ ----------
步骤2_安装Python() {
    echo ""
    echo "[2/9] 安装 Python 3.10+..."
    echo "────────────────────────────────────────"

    # 先检查有没有合适的 python3
    if command -v python3 >/dev/null 2>&1; then
        # 调用库命令：获取 python3 版本号
        # 传入：--version 标志
        # 作用：输出 Python 版本字符串，然后 awk 提取数字部分
        # 传出：Python 版本号（如 3.10.12）
        PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        echo "当前 Python 版本: $PY_VER"
        if [ "$PY_MAJOR" = "3" ] && [ "$PY_MINOR" -ge 10 ]; then
            echo "✅ Python 版本满足要求（≥3.10），跳过安装"
            return
        fi
    fi

    echo "安装 Python 3.11 和 venv/pip..."
    if [ "$OS_FAMILY" = "debian" ]; then
        # Ubuntu 22.04+ 有 python3.11
        if apt-cache search python3.11 >/dev/null 2>&1; then
            $PKG_INSTALL python3.11 python3.11-venv python3.11-dev python3-pip 2>&1 | tail -5
            # 调用库命令：设置 python3 默认指向 python3.11
            # 传入：源路径、目标路径、优先级
            # 作用：更新 alternatives 系统的 python3 默认版本
            # 传出：无返回值
            update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 2>/dev/null || true
        else
            $PKG_INSTALL python3 python3-venv python3-dev python3-pip 2>&1 | tail -5
        fi
    else
        $PKG_INSTALL python3 python3-pip 2>&1 | tail -5
        # RHEL系需要单独装 venv
        $PKG_INSTALL python3-virtualenv 2>&1 | tail -3 || true
    fi

    # 验证
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
    echo "✅ Python 安装完成: $PY_VER"
}

# ---------- 3. 安装 Node.js 18+（构建前端） ----------
步骤3_安装NodeJS() {
    echo ""
    echo "[3/9] 安装 Node.js 18+..."
    echo "────────────────────────────────────────"

    if command -v node >/dev/null 2>&1; then
        # 调用库命令：读取 node 版本
        # 传入：--version 标志
        # 作用：输出 Node.js 版本号
        # 传出：版本字符串
        NODE_VER=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
        echo "当前 Node.js 版本: v$NODE_VER"
        if [ "$NODE_MAJOR" -ge 18 ]; then
            echo "✅ Node.js 版本满足要求（≥18），跳过安装"
            return
        fi
    fi

    echo "通过 NodeSource 安装 Node.js 20 LTS..."
    if [ "$OS_FAMILY" = "debian" ]; then
        # 调用库命令：下载 NodeSource GPG 密钥和源
        # 传入：下载URL
        # 作用：下载并执行 NodeSource 设置脚本，添加 Node.js 20 的 apt 源
        # 传出：执行结果
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>&1 | tail -3
        $PKG_INSTALL nodejs 2>&1 | tail -5
    else
        curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - 2>&1 | tail -3
        $PKG_INSTALL nodejs 2>&1 | tail -5
    fi

    NODE_VER=$(node --version)
    echo "✅ Node.js 安装完成: $NODE_VER"
}

# ---------- 4. 安装并配置 MySQL ----------
步骤4_安装MySQL() {
    echo ""
    echo "[4/9] 安装并配置 MySQL 8.0..."
    echo "────────────────────────────────────────"

    if [ "$BAOTA_MODE" = true ]; then
        echo "ℹ️  宝塔面板模式：跳过 MySQL 安装"
    else
        # 检查 MySQL 是否已安装
        if command -v mysql >/dev/null 2>&1; then
            echo "✅ MySQL 已安装，跳过安装步骤"
        else
            echo "安装 MySQL..."
            if [ "$OS_FAMILY" = "debian" ]; then
                $PKG_INSTALL $MYSQL_PKG 2>&1 | tail -5
                systemctl enable --now mysql 2>/dev/null || systemctl enable --now mysqld 2>/dev/null || true
            else
                if command -v dnf >/dev/null 2>&1; then
                    dnf module enable -y mysql 2>&1 | tail -3 || true
                fi
                $PKG_INSTALL $MYSQL_PKG 2>&1 | tail -5
                systemctl enable --now mysqld 2>/dev/null || systemctl enable --now mysql 2>/dev/null || true
            fi
            sleep 3
        fi

        # 确保 MySQL 已启动
        systemctl start mysql 2>/dev/null || systemctl start mysqld 2>/dev/null || true
        sleep 2
    fi

    # 生成密码（如为空且非常模式）
    if [ "$BAOTA_MODE" != true ]; then
        if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
            MYSQL_ROOT_PASSWORD=$(生成随机密码 16)
            echo "ℹ️  自动生成 MySQL root 密码: $MYSQL_ROOT_PASSWORD"
        fi
    fi
    if [ -z "$MYSQL_APP_PASSWORD" ]; then
        MYSQL_APP_PASSWORD=$(生成随机密码 16)
        echo "ℹ️  自动生成 MySQL 应用用户密码: $MYSQL_APP_PASSWORD"
    fi

    # 配置数据库和用户
    echo "配置 MySQL 数据库和用户..."
    # 调用库命令：执行 MySQL 命令
    # 传入：-u root, -p密码, -e "SQL 语句"
    # 作用：创建数据库、创建用户、授权、刷新权限
    # 传出：SQL 执行结果
    MYSQL_CMD="
        CREATE DATABASE IF NOT EXISTS ${MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
        CREATE USER IF NOT EXISTS '${MYSQL_APP_USER}'@'localhost' IDENTIFIED BY '${MYSQL_APP_PASSWORD}';
        GRANT ALL PRIVILEGES ON ${MYSQL_DB_NAME}.* TO '${MYSQL_APP_USER}'@'localhost';
        FLUSH PRIVILEGES;
    "

    # 依次尝试多种方式连接 MySQL
    连接成功=false
    for 尝试密码 in "" "$MYSQL_ROOT_PASSWORD" "admin" "root"; do
        if [ "$连接成功" = true ]; then break; fi
        if [ -z "$尝试密码" ]; then
            # 无密码尝试
            # 调用库命令：mysql 命令行客户端
            # 传入：-u root, -e "SQL"
            # 作用：执行建库建用户 SQL
            # 传出：执行结果
            echo "  → 尝试无密码登录..."
            mysql -u root -e "$MYSQL_CMD" 2>/dev/null && { echo "  ✅ 无密码登录成功"; 连接成功=true; break; }
        else
            # 有密码尝试
            echo "  → 尝试密码登录 (root / ${尝试密码})..."
            mysql -u root -p"${尝试密码}" -e "$MYSQL_CMD" 2>/dev/null && { echo "  ✅ 密码登录成功"; MYSQL_ROOT_PASSWORD="${尝试密码}"; 连接成功=true; break; }
        fi
    done

    if [ "$连接成功" != true ]; then
        echo "⚠️  MySQL 配置失败，请手动执行以下 SQL:"
        echo "  mysql -u root -p"
        echo "  $MYSQL_CMD"
        echo "  或使用宝塔面板 → 数据库 → 创建数据库 '${MYSQL_DB_NAME}' 和用户 '${MYSQL_APP_USER}'"
    fi

    echo "✅ MySQL 配置完成"
    echo "  数据库名: $MYSQL_DB_NAME"
    echo "  应用用户: $MYSQL_APP_USER"
    echo "  应用密码: $MYSQL_APP_PASSWORD"
}

# ---------- 5. 创建目录并部署代码 ----------
步骤5_准备应用目录() {
    echo ""
    echo "[5/9] 创建应用目录结构..."
    echo "────────────────────────────────────────"

    # 调用库命令：创建多级目录
    # 传入：-p 标志，目录路径
    # 作用：递归创建目录（若不存在），含父目录
    # 传出：无返回值
    mkdir -p "$APP_DIR" "$LOG_DIR" "$PID_DIR" "$BACKUP_DIR"

    # 检查代码是否已经存在
    if [ -f "$APP_DIR/app/主程序.py" ]; then
        echo "✅ 项目代码已存在: $APP_DIR"
    else
        echo "从 GitHub 克隆项目代码..."
        # 调用库命令：git clone
        # 传入：仓库URL, 目标目录
        # 作用：从 GitHub 克隆 Fashiye 代肝平台源码到指定目录
        # 传出：克隆结果
        if command -v git >/dev/null 2>&1; then
            git clone https://github.com/fashiye/fashiye.git "$APP_DIR" 2>&1
        else
            echo "❌ git 未安装，正在安装..."
            $PKG_INSTALL git 2>&1 | tail -3
            git clone https://github.com/fashiye/fashiye.git "$APP_DIR" 2>&1
        fi
        if [ -f "$APP_DIR/app/主程序.py" ]; then
            echo "✅ 从 GitHub 克隆完成"
        else
            echo "❌ 克隆失败，请检查网络或仓库地址"
            exit 1
        fi
    fi

    echo "✅ 应用目录准备完成"
    echo "  APP_DIR:   $APP_DIR"
    echo "  LOG_DIR:   $LOG_DIR"
    echo "  BACKUP:    $BACKUP_DIR"
}

# ---------- 6. 配置环境变量 .env ----------
步骤6_配置环境变量() {
    echo ""
    echo "[6/9] 生成 .env 环境变量文件..."
    echo "────────────────────────────────────────"

    ENV_FILE="$APP_DIR/.env"
    if [ -f "$ENV_FILE" ]; then
        # 备份现有 .env
        cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
        echo "ℹ️  已备份现有 .env 文件"
    fi

    # 生成密钥
    SECRET_KEY=$(生成随机密码 48)
    AES_SECRET=$(生成随机密码 32 | base64 -w0 2>/dev/null || 生成随机密码 32)
    AES_IV=$(生成随机密码 16 | base64 -w0 2>/dev/null || 生成随机密码 16)

    # 服务器公网 IP
    # 调用库命令：HTTP GET 查询公网IP
    # 传入：ifconfig.me 或 ifconfig.co 的URL，超时5秒
    # 作用：查询服务器的公网 IPv4 地址
    # 传出：IP地址字符串
    SERVER_IP=$(curl -s --connect-timeout 5 https://ifconfig.me 2>/dev/null || curl -s --connect-timeout 5 https://api.ipify.org 2>/dev/null || echo "127.0.0.1")
    echo "ℹ️  服务器公网 IP: $SERVER_IP"

    # 调用库函数：写入文件内容
    # 传入：重定向 > ENV_FILE
    # 作用：将所有环境变量以 K=V 格式写入 .env 文件
    # 传出：无返回值
    cat > "$ENV_FILE" <<ENV_EOF
# ==================== Fashiye 生产环境配置 ====================
PROJECT_NAME=Fashiye Game Boosting Platform
VERSION=1.0.0
DEBUG=False

# 安全密钥（部署时自动生成）
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 数据库连接（MySQL）
DATABASE_URL=mysql+aiomysql://${MYSQL_APP_USER}:${MYSQL_APP_PASSWORD}@localhost:3306/${MYSQL_DB_NAME}?charset=utf8mb4

# AES 加密（订单账号信息）
AES_SECRET_KEY=${AES_SECRET}
AES_IV=${AES_IV}

# Redis（可选，不填则禁用）
# REDIS_URL=redis://localhost:6379/0

# 跨域允许
CORS_ORIGINS=*

# ====== 邮件服务器配置（请配置真实的阿里云邮件推送信息） ======
SMTP_HOST=smtpdm.aliyun.com
SMTP_PORT=465
SMTP_USER=Leaf_Wolf@fashiye.cn
SMTP_PASSWORD=Aa2b9Xk8Lm3P
SMTP_FROM=Leaf_Wolf@fashiye.cn

# ====== iaitouzi 聚合支付配置（请填写真实信息） ======
IAITOUZI_APP_ID=2258
IAITOUZI_APP_SECRET=2e3a2376-63bb-11f1-b952-0242ac11
IAITOUZI_BASE_URL=https://iaitouzi.com/core/api/request/pay/
# 回调通知地址（服务器有公网IP后改这个）
IAITOUZI_NOTIFY_URL=http://${SERVER_IP}/api/v1/payment/callback
ENV_EOF

    chmod 600 "$ENV_FILE"
    echo "✅ .env 文件已生成: $ENV_FILE"
    echo "  ⚠️  注意：邮件和支付密钥已用占位默认值，请到 iaitouzi/阿里云 后台获取真实值后修改"
}

# ---------- 7. 安装 Python 虚拟环境和依赖 ----------
步骤7_安装Python依赖() {
    echo ""
    echo "[7/9] 安装 Python 虚拟环境和依赖..."
    echo "────────────────────────────────────────"

    cd "$APP_DIR"

    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        # 调用库命令：创建 Python 虚拟环境
        # 传入：-m venv, 目录名 venv
        # 作用：在项目根目录创建独立的 Python 虚拟环境，隔离全局包
        # 传出：执行结果
        python3 -m venv venv
        echo "✅ 虚拟环境创建: $APP_DIR/venv"
    else
        echo "ℹ️  虚拟环境已存在，跳过创建"
    fi

    # 激活虚拟环境并安装依赖
    # 传入：venv/bin/activate 脚本
    # 作用：使当前 shell 会话使用虚拟环境中的 python/pip
    # 传出：无返回值（修改当前 shell 的 PATH）
    source "$APP_DIR/venv/bin/activate"

    # 先升级 pip
    # 调用库命令：升级 pip
    # 传入：pip install --upgrade pip
    # 作用：将虚拟环境中的 pip 升级到最新版
    # 传出：执行结果
    pip install --upgrade pip -q 2>&1 | tail -1

    # 安装 requirements
    if [ -f "$APP_DIR/requirements.txt" ]; then
        echo "安装 Python 依赖包（约需 2-5 分钟）..."
        # 调用库命令：pip 安装依赖
        # 传入：-r requirements.txt, --no-cache-dir
        # 作用：读取 requirements.txt 中的包列表并逐一安装到虚拟环境
        # 传出：执行结果
        pip install --no-cache-dir -r "$APP_DIR/requirements.txt" 2>&1 | tail -5
        echo "✅ Python 依赖安装完成"
    else
        echo "❌ 未找到 requirements.txt，请确认代码完整"
        exit 1
    fi
}

# ---------- 8. 同步数据库 + 构建前端 ----------
步骤8_同步数据库构建前端() {
    echo ""
    echo "[8/9] 同步数据库表结构 + 构建前端..."
    echo "────────────────────────────────────────"

    cd "$APP_DIR"
    source "$APP_DIR/venv/bin/activate"

    # 同步数据库表结构
    echo "同步数据库表结构..."
    # 调用库命令：执行 Python 脚本
    # 传入：-c "代码字符串"
    # 作用：在 Python 中通过 SQLAlchemy 建表
    # 传出：执行结果
    python3 -c "
import asyncio
from app.数据库.会话 import 数据库基类 as Base, 引擎 as engine

async def 建表():
    async with engine.begin() as conn:
        # 调用库方法：同步建表
        # 传入：Base.metadata（所有模型的元数据集合）
        # 作用：遍历所有 ORM 模型，在数据库中创建对应表（不存在时）
        # 传出：无返回值
        await conn.run_sync(Base.metadata.create_all)
    print('✓ 所有表已创建')

asyncio.run(建表())
" 2>&1 | tail -3

    # 构建前端
    if [ -d "$APP_DIR/frontend" ] && [ -f "$APP_DIR/frontend/package.json" ]; then
        echo "构建前端项目..."
        cd "$APP_DIR/frontend"

        # 安装 npm 依赖
        if [ ! -d "node_modules" ]; then
            echo "  → 安装 npm 依赖（约需 1-3 分钟）..."
            # 调用库命令：npm 安装依赖
            # 传入：install 或 ci --no-audit
            # 作用：根据 package.json 安装前端所有 npm 包到 node_modules
            # 传出：执行结果
            npm ci --no-audit --no-fund --loglevel=error 2>&1 | tail -3 || \
            npm install --no-audit --no-fund --loglevel=error 2>&1 | tail -3
        else
            echo "  → node_modules 已存在，跳过 npm install"
        fi

        # 构建
        echo "  → 执行 npm run build..."
        # 调用库命令：npm 构建
        # 传入：run build
        # 作用：执行 Vite 构建，将 React 源码打包为静态文件到 dist/
        # 传出：执行结果
        npm run build 2>&1 | tail -5

        if [ -d "dist" ]; then
            echo "✅ 前端构建完成: $APP_DIR/frontend/dist/"
        else
            echo "❌ 前端构建失败，dist 目录未生成"
            exit 1
        fi
    else
        echo "⚠️  未找到 frontend 目录，跳过前端构建"
    fi
}

# ---------- 9. 安装 Nginx + 配置 + 配置 systemd ----------
步骤9_配置Nginx和Systemd() {
    echo ""
    echo "[9/9] 配置 Nginx 和 systemd 服务..."
    echo "────────────────────────────────────────"

    # --- Nginx 配置（宝塔模式用宝塔目录，普通模式安装+配置） ---
    if [ "$BAOTA_MODE" = true ]; then
        echo "ℹ️  宝塔面板模式：跳过 Nginx 安装"
        # 宝塔的 Nginx 配置文件目录
        NGINX_CONF_DIR="$BAOTA_NGINX_VHOST"
        mkdir -p "$NGINX_CONF_DIR"
        NGINX_CONF_FILE="${NGINX_CONF_DIR}/${APP_NAME}.conf"
    else
        # 安装 Nginx
        if ! command -v nginx >/dev/null 2>&1; then
            echo "安装 Nginx..."
            $PKG_INSTALL $NGINX_PKG 2>&1 | tail -3
        fi
        echo "✅ Nginx 已安装"

        NGINX_CONF_FILE="/etc/nginx/sites-available/$APP_NAME"
        if [ "$OS_FAMILY" = "rhel" ]; then
            NGINX_CONF_FILE="/etc/nginx/conf.d/${APP_NAME}.conf"
        fi
        # 确保配置目录存在
        mkdir -p "$(dirname "$NGINX_CONF_FILE")"
    fi

    echo "生成 Nginx 配置: $NGINX_CONF_FILE"

    # 处理域名/IP的 HTTP-only 配置（无SSL证书，避免SSL启动失败）
    if [ -z "$DOMAIN" ]; then
        # === 无域名，使用 IP，纯 HTTP 模式 ===
        cat > "$NGINX_CONF_FILE" <<NGINX_IP
upstream fashiye_backend {
    server 127.0.0.1:8888;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name _;

    client_max_body_size 50m;

    # 日志
    access_log ${LOG_DIR}/nginx_access.log;
    error_log  ${LOG_DIR}/nginx_error.log;

    # ============ 前端静态文件 ============
    location / {
        root ${APP_DIR}/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # ============ API 反向代理 ============
    location /api/ {
        proxy_pass http://fashiye_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";

        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    300s;

        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # ============ WebSocket ============
    location /ws/ {
        proxy_pass http://fashiye_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 3600s;
    }

    # ============ 静态资源缓存 ============
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root ${APP_DIR}/frontend/dist;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # ============ 安全头 ============
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ============ Gzip ============
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml application/atom+xml image/svg+xml;
}
NGINX_IP
        echo "  → 使用 IP 模式（HTTP-only，无SSL）"
    else
        # === 有域名，使用 HTTPS + Let's Encrypt 自动证书（先写 HTTP，后 certbot 升级）===
        cat > "$NGINX_CONF_FILE" <<NGINX_DOMAIN
upstream fashiye_backend {
    server 127.0.0.1:8888;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    # Let's Encrypt 验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 其他重定向到 HTTPS（有证书后生效）
    location / {
        # return 301 https://\$host\$request_uri;  # 证书到手后取消注释
        # 暂时先 HTTP 转发
        proxy_pass http://fashiye_backend;
        proxy_set_header Host \$host;
    }
}
NGINX_DOMAIN
        echo "  → 使用域名模式: $DOMAIN（部署后建议手动运行 certbot --nginx -d $DOMAIN 开启HTTPS）"
    fi

    # 非宝塔模式：启用站点
    if [ "$BAOTA_MODE" != true ]; then
        # Debian/Ubuntu：启用站点，禁用默认
        if [ "$OS_FAMILY" = "debian" ]; then
            ln -sf "$NGINX_CONF_FILE" "/etc/nginx/sites-enabled/$APP_NAME"
            rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
        fi

        # 测试 nginx 配置
        if nginx -t 2>&1 | grep -q "syntax is ok\|test is successful"; then
            echo "✅ Nginx 配置语法正确"
            systemctl enable nginx 2>/dev/null || true
            systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
        else
            echo "⚠️  Nginx 配置有问题，请手动检查:"
            nginx -t 2>&1
        fi
    else
        echo "ℹ️  宝塔模式：Nginx 配置已生成到 ${NGINX_CONF_FILE}"
        echo "   请在宝塔面板 → 网站 → 添加站点（或配置已有站点），使用此配置内容"
    fi

    # ---- 配置 systemd 服务 ----
    SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

    # 修复 start.sh 中的 APP_DIR 路径
    if [ -f "$APP_DIR/scripts/start.sh" ]; then
        # 调用库命令：替换文件内容
        # 传入：sed -i s|旧值|新值| 文件
        # 作用：将 start.sh 中旧的 APP_DIR 硬编码路径替换为当前正确路径
        # 传出：无返回值
        sed -i "s|APP_DIR=\"/www/wwwroot/fashiye\"|APP_DIR=\"${APP_DIR}\"|g" "$APP_DIR/scripts/start.sh"
        sed -i "s|GUNICORN_BIND=.*|GUNICORN_BIND=\"${GUNICORN_BIND}\"|g" "$APP_DIR/scripts/start.sh"
        sed -i "s|GUNICORN_WORKERS=.*|GUNICORN_WORKERS=\"${GUNICORN_WORKERS}\"|g" "$APP_DIR/scripts/start.sh"
        chmod +x "$APP_DIR/scripts/"*.sh 2>/dev/null || true
    fi

    # 创建 www-data 用户（如果不存在）
    # 调用库命令：创建系统用户
    # 传入：useradd -r -s /usr/sbin/nologin www-data
    # 作用：创建用于运行 Web 服务的低权限用户 www-data
    # 传出：无返回值
    id www-data >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin www-data 2>/dev/null || true

    # 写入 systemd service 文件
    cat > "$SERVICE_FILE" <<SERVICE_EOF
[Unit]
Description=Fashiye Game Boosting Platform
After=network.target mysql.service nginx.service
Wants=mysql.service nginx.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}

# 虚拟环境中的 gunicorn
ExecStart=${APP_DIR}/venv/bin/gunicorn app.主程序:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${GUNICORN_WORKERS} \
    --bind ${GUNICORN_BIND} \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 10000 \
    --max-requests-jitter 1000 \
    --access-logfile ${LOG_DIR}/access.log \
    --error-logfile ${LOG_DIR}/error.log \
    --log-level info

ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID

Restart=always
RestartSec=5

Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=${APP_DIR}

LimitNOFILE=65535
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    # 赋予运行目录权限
    # 调用库命令：递归修改目录所有者
    # 传入：-R 用户:组 目录
    # 作用：将项目目录和日志目录的所有者改为 www-data，使其能写入日志
    # 传出：无返回值
    chown -R www-data:www-data "$APP_DIR" "$LOG_DIR" "$PID_DIR" 2>/dev/null || true
    chmod -R u+rwX "$APP_DIR" "$LOG_DIR" "$PID_DIR" 2>/dev/null || true

    # 加载 systemd 并启动
    # 调用库命令：重载 systemd 配置
    # 传入：daemon-reload
    # 作用：扫描 /etc/systemd/system 下的 .service 文件变更，使新配置生效
    # 传出：无返回值
    systemctl daemon-reload
    # 调用库命令：开机自启
    # 传入：enable fashiye
    # 作用：将 fashiye.service 设置为开机自动启动
    # 传出：无返回值
    systemctl enable "$APP_NAME" 2>/dev/null || true
    echo "  → 启动后端服务 (${APP_NAME})..."
    # 调用库命令：启动服务
    # 传入：restart fashiye
    # 作用：重启 fashiye systemd 服务（即使未运行也会启动）
    # 传出：无返回值
    systemctl restart "$APP_NAME" 2>/dev/null || true
    sleep 4

    # 检查服务状态
    # 传入：is-active fashiye
    # 作用：查询 fashiye 服务当前是否处于 active 状态
    # 传出：active / inactive / failed
    if systemctl is-active --quiet "$APP_NAME"; then
        echo "✅ 后端服务 (${APP_NAME}): 运行中"
    else
        echo "❌ 后端服务启动失败，查看日志:"
        echo "   journalctl -u ${APP_NAME} -n 30 --no-pager"
        journalctl -u "$APP_NAME" -n 20 --no-pager 2>&1 || true
    fi

    # 重启 Nginx 最终确认
    if [ "$BAOTA_MODE" != true ]; then
        systemctl restart nginx 2>/dev/null || true
        if systemctl is-active --quiet nginx; then
            echo "✅ Nginx 服务: 运行中"
        else
            echo "⚠️  Nginx 未运行，请检查"
        fi
    else
        echo "ℹ️  宝塔模式：请在宝塔面板中重载 Nginx 使配置生效"
    fi
}

# ---------- 10. 配置自动更新（cron 定时从 GitHub 拉取） ----------
步骤10_配置自动更新() {
    echo ""
    echo "[10/10] 配置自动更新（cron 定时任务）..."
    echo "────────────────────────────────────────"

    AUTO_SCRIPT="${APP_DIR}/scripts/auto_update.sh"

    # 确保脚本存在
    if [ -f "$AUTO_SCRIPT" ]; then
        chmod +x "$AUTO_SCRIPT"
        echo "✅ 自动更新脚本已就绪: $AUTO_SCRIPT"
    else
        echo "⚠️  未找到 $AUTO_SCRIPT，跳过自动更新配置"
        return
    fi

    # 写入 cron 任务（每小时执行一次）
    # 调用库命令：crontab -l 列出当前 crontab
    # 传入：-l
    # 作用：列出当前用户的 crontab 内容，用于检查是否已有该任务
    # 传出：crontab 内容
    定时任务内容=$(crontab -l 2>/dev/null || echo "")
    if echo "$定时任务内容" | grep -q "auto_update.sh"; then
        echo "ℹ️  自动更新定时任务已存在，跳过"
    else
        # 调用库命令：crontab 写入
        # 传入：临时文件或管道
        # 作用：在 crontab 中追加一行，每小时执行一次 auto_update.sh
        # 传出：无返回值
        (echo "$定时任务内容"; echo "0 * * * * cd ${APP_DIR} && bash ${AUTO_SCRIPT} >> ${LOG_DIR}/cron_auto_update.log 2>&1") | crontab -
        echo "✅ 已添加 cron 定时任务：每小时检查更新"
    fi

    echo "   手动执行: bash $AUTO_SCRIPT"
    echo "   查看日志: tail -f ${LOG_DIR}/auto_update.log"
}

# ==================== 主流程 ====================
检测操作系统

步骤1_安装基础依赖
步骤2_安装Python
步骤3_安装NodeJS
步骤4_安装MySQL
步骤5_准备应用目录
步骤6_配置环境变量
步骤7_安装Python依赖
步骤8_同步数据库构建前端
步骤9_配置Nginx和Systemd
步骤10_配置自动更新

# ==================== 总结输出 ====================
SERVER_IP_FINAL=$(curl -s --connect-timeout 5 https://ifconfig.me 2>/dev/null || echo "你的服务器IP")

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     🎉 部署完成！恭喜！                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 访问地址:  http://${SERVER_IP_FINAL}"
if [ -n "$DOMAIN" ]; then
    echo "   域名访问:  http://${DOMAIN}  (解析A记录到 ${SERVER_IP_FINAL})"
    echo "   HTTPS 一键: certbot --nginx -d ${DOMAIN}"
fi
echo ""
echo "📋 常用命令:"
if [ "$BAOTA_MODE" != true ]; then
    echo "   查看状态:  systemctl status ${APP_NAME} nginx"
fi
echo "   重启服务:  systemctl restart ${APP_NAME}"
echo "   实时日志:  journalctl -u ${APP_NAME} -f"
echo "   访问日志:  tail -f ${LOG_DIR}/access.log"
echo "   错误日志:  tail -f ${LOG_DIR}/error.log"
echo "   自动更新日志: tail -f ${LOG_DIR}/auto_update.log"
echo "   手动更新:  bash ${APP_DIR}/scripts/auto_update.sh"
echo "   备份数据:  bash ${APP_DIR}/scripts/backup.sh"
echo ""
echo "🔐 重要凭据（请妥善保存）:"
echo "   MySQL root 密码:        ${MYSQL_ROOT_PASSWORD}"
echo "   MySQL 应用用户密码:     ${MYSQL_APP_PASSWORD}"
echo "   应用 .env 位于:         ${APP_DIR}/.env"
echo ""
echo "⚠️  请记得修改以下配置（在 ${APP_DIR}/.env 中）:"
echo "   1. SMTP_PASSWORD   → 阿里云邮件推送真实密码"
echo "   2. IAITOUZI_APP_SECRET → iaitouzi 支付后台真实密钥"
echo "   3. IAITOUZI_NOTIFY_URL → 改为你的域名/公网IP对应的回调地址"
echo ""

# 将凭据写入文件方便回溯
CREDS_FILE="/root/fashiye_credentials_$(date +%Y%m%d).txt"
cat > "$CREDS_FILE" <<CREDS_EOF
# Fashiye 部署凭据 $(date)
SERVER_IP=${SERVER_IP_FINAL}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
MYSQL_APP_USER=${MYSQL_APP_USER}
MYSQL_APP_PASSWORD=${MYSQL_APP_PASSWORD}
MYSQL_DB_NAME=${MYSQL_DB_NAME}
APP_DIR=${APP_DIR}
ENV_FILE=${APP_DIR}/.env
CREDS_EOF
chmod 600 "$CREDS_FILE"
echo "💾 凭据已备份到: $CREDS_FILE"
echo ""
