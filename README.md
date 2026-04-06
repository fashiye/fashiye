# Fashiye - 游戏代练交易平台

一个完整的游戏代练交易平台，支持用户发布订单、打手接单、管理员审核等功能。

## 功能特性

- 用户注册、登录、认证
- 订单发布与管理
- 订单审核系统
- 打手接单系统
- 实时消息系统
- 管理员后台

## 技术栈

- 后端: FastAPI + SQLAlchemy + MySQL
- 前端: React + Vite
- 认证: JWT
- 部署: Nginx + Systemd

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+

### 安装

1. 克隆仓库
```bash
git clone https://github.com/your-username/fashiye.git
cd fashiye
```

2. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置数据库连接等
```

3. 安装后端依赖
```bash
pip install -r requirements.txt
```

4. 安装前端依赖并构建
```bash
cd frontend
npm install
npm run build
cd ..
```

5. 初始化数据库
```bash
python init_db.py
python seed_games.py
python create_admin.py
```

6. 启动服务
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8888
```

## 部署

详细部署说明请查看 [scripts/DEPLOY.md](scripts/DEPLOY.md)

## 目录结构

```
fashiye/
├── app/                 # 后端应用
│   ├── api/            # API路由
│   ├── core/           # 核心配置
│   ├── db/             # 数据库
│   ├── models/         # 数据模型
│   ├── schemas/        # Pydantic模型
│   ├── services/       # 业务逻辑
│   └── utils/          # 工具函数
├── frontend/           # 前端应用
├── scripts/            # 部署脚本
└── alembic/            # 数据库迁移
```

## License

MIT
