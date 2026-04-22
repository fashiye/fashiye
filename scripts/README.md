# 管理员账号管理脚本

本目录包含用于管理游戏代练平台管理员账号的实用脚本。

## 可用脚本

### `create_admin.py` - 创建管理员账号

用于在后台创建管理员账号，支持超级管理员和运营管理员角色。

#### 功能特性
- ✅ 创建超级管理员 (`super`) 或运营管理员 (`operator`)
- ✅ 检查用户名和邮箱是否已存在
- ✅ 密码自动使用 Argon2 哈希加密存储
- ✅ 支持设置账号状态（启用/禁用）
- ✅ 支持设置头像URL

#### 使用方法

```bash
# 从项目根目录运行
python scripts/create_admin.py --username admin --email admin@example.com --password Admin@123 --role super

# 创建运营管理员
python scripts/create_admin.py --username operator --email operator@example.com --password Operator@123 --role operator

# 创建禁用状态的管理员
python scripts/create_admin.py --username testadmin --email test@example.com --password Test@123 --role operator --status 0

# 创建带头像的管理员
python scripts/create_admin.py --username admin3 --email admin3@example.com --password Admin@123 --role super --avatar https://example.com/avatar.jpg
```

#### 参数说明

| 参数 | 必填 | 说明 | 默认值 | 可选值 |
|------|------|------|--------|--------|
| `--username` | 是 | 管理员用户名 | - | 任意字符串 |
| `--email` | 是 | 管理员邮箱 | - | 合法邮箱格式 |
| `--password` | 是 | 管理员密码 | - | 建议使用强密码 |
| `--role` | 否 | 管理员角色 | `operator` | `super`, `operator` |
| `--status` | 否 | 账号状态 | `1` (启用) | `0` (禁用), `1` (启用) |
| `--avatar` | 否 | 头像URL | `None` | 任意有效URL |

#### 输出示例

```
正在创建管理员账号...
用户名: admin2
邮箱: admin2@example.com
角色: super
状态: 启用
--------------------------------------------------
✅ 管理员账号创建成功

账号信息:
  ID: 4
  用户名: admin2
  邮箱: admin2@example.com
  角色: super
  状态: 启用
  创建时间: 2026-04-20T12:50:08
```

#### 错误处理

脚本会检查以下情况并给出友好提示：
- ❌ 用户名已存在
- ❌ 邮箱已存在
- ❌ 无效的角色
- ❌ 无效的状态值
- ❌ 数据库连接失败

#### 环境要求

脚本使用与主应用相同的数据库配置，需要确保：
1. `.env` 文件已正确配置 `DATABASE_URL`
2. 数据库服务正在运行
3. `admins` 表已存在（通过 Alembic 迁移创建）

#### 注意事项

1. **密码安全**
   - 密码会通过 Argon2 算法哈希后存储
   - 建议使用强密码（包含大小写字母、数字、特殊字符）
   - 脚本不会存储或记录明文密码

2. **权限分配**
   - `super` (超级管理员): 拥有所有权限，可管理其他管理员
   - `operator` (运营管理员): 拥有日常运营权限，如审核订单、管理用户等

3. **首次部署**
   建议在首次部署应用后立即创建至少一个超级管理员账号：
   ```bash
   python scripts/create_admin.py --username admin --email admin@yourdomain.com --password "StrongPassword@123" --role super
   ```

## 数据库表结构参考

管理员账号存储在 `admins` 表中，表结构如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| username | VARCHAR(50) | 用户名，唯一 |
| email | VARCHAR(100) | 邮箱，唯一 |
| password | VARCHAR(255) | 哈希后的密码 |
| avatar | VARCHAR(255) | 头像URL |
| role | ENUM('super', 'operator') | 管理员角色 |
| status | TINYINT | 状态：0-禁用，1-启用 |
| last_login_at | DATETIME | 最后登录时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 相关文件

- `../app/models/user.py` - 管理员模型定义
- `../app/core/security.py` - 密码哈希函数
- `../app/db/session.py` - 数据库会话管理
- `../.env.example` - 环境变量示例