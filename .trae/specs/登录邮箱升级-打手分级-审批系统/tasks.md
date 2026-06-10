# 游戏代练交易平台 - 登录邮箱升级、打手分级、审批系统 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 1: 修改用户模型（去除用户名字段唯一约束）
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 去除 User.username、Handler.username、Admin.username 字段的 unique 约束
  - 保持 email 字段的 unique 约束不变
  - 创建数据库迁移脚本
- **Acceptance Criteria Addressed**: AC-2
- **Test Requirements**:
  - `programmatic` TR-1.1: 多个用户可以使用相同 username 但不同 email 注册
  - `programmatic` TR-1.2: 重复 email 仍然会被拒绝
- **Notes**: 需要创建 Alembic 迁移脚本

## [ ] Task 2: 修改登录逻辑（改为邮箱登录）
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 修改 UserLogin schema，username 改为 email
  - 修改 /auth/login 接口，改为使用 email 查找用户
  - 更新前端登录页面
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: 使用邮箱+密码可以登录成功
  - `programmatic` TR-2.2: 使用不存在邮箱会返回错误
- **Notes**: 需要同时修改 User/Handler/Admin 三个表的查询

## [ ] Task 3: 新增打手注册审批机制
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 在 Handler 表新增 status 字段的枚举支持：0=待审批，1=已通过，2=已拒绝，3=禁用
  - 修改注册逻辑：打手注册时 status 设为 0（待审批）
  - 修改登录验证：待审批或拒绝的打手无法登录
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-3.1: 打手注册后默认状态是待审批
  - `programmatic` TR-3.2: 待审批打手无法登录
  - `programmatic` TR-3.3: 已通过打手可以正常登录
- **Notes**: 保持用户和管理员的 status 逻辑不变

## [ ] Task 4: 创建游戏等级体系表（管理员自定义）
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 新建 GameLevel 表：id, game_id, name, sort, status, created_at, updated_at
  - 每个游戏可有多个等级（如：青铜、白银、黄金、白金、钻石）
  - 等级顺序由 sort 字段控制
  - 创建对应的 SQLAlchemy 模型
  - 创建 Alembic 迁移脚本
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-4.1: 管理员可以为每个游戏添加多个等级
  - `programmatic` TR-4.2: 等级可以设置名称和排序
  - `programmatic` TR-4.3: 每个游戏的等级独立管理
- **Notes**: name 字段如"青铜""白银""黄金"，sort 控制显示顺序

## [ ] Task 5: 创建打手游戏等级映射表
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 新建 HandlerGameLevel 表：id, handler_id, game_id, game_level_id, created_at, updated_at
  - 记录打手在每个游戏中的当前等级
  - 创建对应的 SQLAlchemy 模型
  - 创建 Alembic 迁移脚本
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-5.1: 可以为打手设置某游戏的等级
  - `programmatic` TR-5.2: 每个打手在每个游戏只能有一个当前等级
  - `programmatic` TR-5.3: 查询打手能获取其所有游戏等级
- **Notes**: 默认等级为该游戏的第一个等级

## [ ] Task 6: 新增游戏等级管理 API
- **Priority**: P1
- **Depends On**: Task 4
- **Description**: 
  - 在 games 路由下新增 /games/{game_id}/levels 路由
  - GET /games/{game_id}/levels: 获取游戏的等级列表
  - POST /games/{game_id}/levels: 为游戏添加等级
  - PUT /games/{game_id}/levels/{level_id}: 修改等级
  - DELETE /games/{game_id}/levels/{level_id}: 删除等级
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-6.1: 管理员可以为游戏添加/编辑/删除等级
  - `programmatic` TR-6.2: 等级按 sort 字段排序
  - `programmatic` TR-6.3: 删除等级时检查是否有打手使用该等级

## [ ] Task 7: 新增打手管理后端 API
- **Priority**: P1
- **Depends On**: Task 3, Task 5
- **Description**: 
  - 创建 /handlers 路由组
  - GET /handlers: 分页获取打手列表，支持状态筛选
  - PUT /handlers/{handler_id}/status: 审批/禁用打手
  - PUT /handlers/{handler_id}/game-levels: 设置打手游戏等级
  - GET /handlers/{handler_id}: 获取打手详情（包含等级信息）
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-6
- **Test Requirements**:
  - `programmatic` TR-7.1: 管理员可以查看打手列表
  - `programmatic` TR-7.2: 可以审批通过/拒绝打手
  - `programmatic` TR-7.3: 可以设置打手游戏等级
  - `programmatic` TR-7.4: 打手详情包含其所有游戏等级

## [ ] Task 8: 拆分用户管理 API
- **Priority**: P1
- **Depends On**: None
- **Description**: 
  - 修改 /users 接口：只返回用户（玩家）数据
  - 新增 /admin/users 接口（可选）
  - 更新响应 schema
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `programmatic` TR-8.1: 用户管理接口只包含玩家
  - `programmatic` TR-8.2: 打手管理只在 /handlers 接口返回
- **Notes**: 保持现有 /users 接口兼容性或逐步迁移

## [ ] Task 9: 更新前端登录注册页面
- **Priority**: P1
- **Depends On**: Task 2, Task 3
- **Description**: 
  - 修改 Login.jsx：将输入字段从用户名改为邮箱
  - 修改 Register.jsx：提示打手注册需要审批
  - 更新表单验证逻辑
- **Acceptance Criteria Addressed**: AC-1, AC-5
- **Test Requirements**:
  - `human-judgement` TR-9.1: 登录页面显示邮箱输入框
  - `human-judgement` TR-9.2: 注册打手时有提示需要审批

## [ ] Task 10: 创建前端打手管理页面
- **Priority**: P1
- **Depends On**: Task 7, Task 8
- **Description**: 
  - 创建 AdminHandlers.jsx：打手管理页面
  - 创建 AdminHandlerDetail.jsx：打手详情页（可设置等级）
  - 更新 AdminDashboard.jsx：添加打手管理入口
  - 修改 AdminUsers.jsx：只显示玩家用户
- **Acceptance Criteria Addressed**: AC-4, AC-6
- **Test Requirements**:
  - `human-judgement` TR-10.1: 后台有独立的打手管理入口
  - `human-judgement` TR-10.2: 用户管理只显示玩家
  - `human-judgement` TR-10.3: 打手管理可以审批和设置等级

## [ ] Task 11: 游戏等级管理前端
- **Priority**: P2
- **Depends On**: Task 6
- **Description**: 
  - 在游戏管理页面添加等级管理功能
  - 管理员可以增删改游戏等级
  - 关联的打手等级分布查看
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `human-judgement` TR-11.1: 游戏管理能看到相关打手等级
- **Notes**: 此任务为可选增强功能

## [ ] Task 12: 数据库迁移和数据兼容性
- **Priority**: P0
- **Depends On**: Task 1, Task 4, Task 5
- **Description**: 
  - 创建 Alembic 迁移脚本
  - 测试数据迁移
  - 确保现有数据兼容
- **Acceptance Criteria Addressed**: NFR-2
- **Test Requirements**:
  - `programmatic` TR-12.1: 迁移脚本能正常执行
  - `programmatic` TR-12.2: 现有数据不会丢失
