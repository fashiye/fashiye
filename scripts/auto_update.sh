#!/bin/bash
# =============================================================================
# Fashiye 自动更新脚本
# 用途：从 GitHub 拉取最新代码 → 更新依赖 → 构建前端 → 重启服务
# 建议通过 cron 定时执行（如每小时一次）
# 用法：bash auto_update.sh
# =============================================================================
set -e

APP_DIR="/www/wwwroot/fashiye"
LOG_FILE="${APP_DIR}/logs/auto_update.log"
VENV_DIR="${APP_DIR}/venv"
SERVICE_NAME="fashiye"

# 日志函数：输出到控制台和日志文件
写日志() {
    # 传入：日志内容字符串
    # 作用：追加时间戳并将消息同时输出到标准输出和日志文件
    # 传出：无返回值
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# 目录预处理：确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

写日志 "===== 自动更新开始 ====="

# ---------- 1. 进入项目目录 ----------
cd "$APP_DIR"

# ---------- 2. 记录当前提交哈希 ----------
# 调用库命令：git rev-parse
# 传入：HEAD
# 作用：获取当前 HEAD 的完整 commit hash，用于比较是否有新提交
# 传出：commit hash 字符串
旧提交哈希=$(git rev-parse HEAD 2>/dev/null || echo "")

# ---------- 3. 拉取最新代码 ----------
写日志 "正在拉取 GitHub 最新代码..."
# 调用库命令：git pull
# 传入：origin 主分支
# 作用：从远程 GitHub 仓库拉取最新的代码变更
# 传出：拉取结果
拉取结果=$(git pull origin main 2>&1) || {
    拉取退出码=$?
    写日志 "⚠️  git pull 失败: $拉取结果"
    # 可能是分支名不同（master 而非 main），重试
    拉取结果=$(git pull origin master 2>&1) || {
        写日志 "⚠️  git pull master 也失败，跳过本次更新"
        exit 1
    }
}

# ---------- 4. 检查是否有更新 ----------
新提交哈希=$(git rev-parse HEAD)
if [ "$旧提交哈希" = "$新提交哈希" ]; then
    写日志 "✅ 代码已是最新，无需更新"
    echo ""
    exit 0
fi

写日志 "📦 检测到新提交，开始更新流程..."

# ---------- 5. 安装/更新 Python 依赖 ----------
if [ -f "$APP_DIR/requirements.txt" ]; then
    # 检查 requirements.txt 是否有变化
    # 调用库命令：git diff
    # 传入：旧哈希 新哈希 -- requirements.txt
    # 作用：比较两次提交之间 requirements.txt 的差异
    # 传出：diff 内容
    if git diff "$旧提交哈希" "$新提交哈希" -- requirements.txt | grep -q "^[+-]" ; then
        写日志 "📦 requirements.txt 有变更，更新 Python 依赖..."
        if [ -f "$VENV_DIR/bin/activate" ]; then
            # 调用库命令：source 激活虚拟环境
            # 传入：venv/bin/activate
            # 作用：激活 Python 虚拟环境，使 pip 操作在虚拟环境中执行
            # 传出：无返回值（修改当前 shell PATH）
            source "$VENV_DIR/bin/activate"
            # 调用库命令：pip install 安装依赖
            # 传入：-r requirements.txt
            # 作用：安装/更新 requirements.txt 中列出的所有 Python 包
            # 传出：安装结果
            pip install --no-cache-dir -r "$APP_DIR/requirements.txt" 2>&1 | tail -5
            写日志 "✅ Python 依赖更新完成"
        else
            写日志 "⚠️  虚拟环境不存在，跳过 Python 依赖更新"
        fi
    fi
fi

# ---------- 6. 构建前端 ----------
if [ -d "$APP_DIR/frontend" ] && [ -f "$APP_DIR/frontend/package.json" ]; then
    # 检查 frontend 目录是否有变更
    if git diff "$旧提交哈希" "$新提交哈希" -- frontend/ | grep -q "^[+-]" ; then
        写日志 "🎨 前端代码有变更，重新构建..."
        cd "$APP_DIR/frontend"

        # 检查是否需要更新 npm 依赖
        if git diff "$旧提交哈希" "$新提交哈希" -- frontend/package.json frontend/package-lock.json | grep -q "^[+-]" ; then
            写日志 "  → package.json 有变化，更新 npm 依赖..."
            # 调用库命令：npm ci 安装依赖
            # 传入：--no-audit --no-fund
            # 作用：根据 package-lock.json 精确安装前端依赖
            # 传出：安装结果
            npm ci --no-audit --no-fund --loglevel=error 2>&1 || npm install --no-audit --no-fund --loglevel=error 2>&1
        fi

        # 调用库命令：npm run build 构建前端
        # 传入：run build
        # 作用：执行 Vite 构建，生成生产环境的静态文件到 dist/
        # 传出：构建结果
        if npm run build 2>&1 | tee -a "$LOG_FILE" | tail -5; then
            写日志 "✅ 前端构建完成"
        else
            写日志 "❌ 前端构建失败，请手动检查"
            # 即使前端构建失败，后端仍可运行，不退出
        fi
    fi
fi

# ---------- 7. 重启后端服务 ----------
写日志 "🔄 重启后端服务 ${SERVICE_NAME}..."
# 调用库命令：systemctl restart 重启服务
# 传入：restart fashiye
# 作用：重启 fashiye systemd 服务，使新代码生效
# 传出：无返回值
systemctl restart "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"

# 等待服务启动
sleep 3

# 检查服务状态
# 调用库命令：systemctl is-active
# 传入：fashiye
# 作用：查询 fashiye 服务是否正在运行
# 传出：active / inactive / failed
if systemctl is-active --quiet "$SERVICE_NAME"; then
    写日志 "✅ 服务重启成功，运行中"
else
    写日志 "❌ 服务重启失败，查看日志: journalctl -u ${SERVICE_NAME} -n 30 --no-pager"
fi

写日志 "===== 自动更新完成 ====="
echo ""
