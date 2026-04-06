# 多项目订单功能实现任务

## 任务列表

### [x] 任务1: 数据库变更 - 新增 order_items 表
- **优先级**: P0
- **依赖**: 无
- **描述**:
  - 创建 order_items 表存储订单项目明细
  - 修改 orders 表，移除 project_id, quantity, unit_price 等字段
- **子任务**:
  - [x] 编写 Alembic migration 脚本创建 order_items 表
  - [x] 编写 Alembic migration 脚本调整 orders 表结构
  - [x] 创建 OrderItem 模型类
  - [x] 修改 Order 模型，添加与 OrderItem 的关系

### [x] 任务2: 后端 Schema 变更
- **优先级**: P0
- **依赖**: 任务1
- **描述**:
  - 修改 OrderCreate schema 支持 items 列表
  - 修改 OrderResponse schema 返回 items 列表
- **子任务**:
  - [x] 创建 OrderItemCreate schema
  - [x] 创建 OrderItemResponse schema
  - [x] 修改 OrderCreate schema
  - [x] 修改 OrderResponse schema

### [x] 任务3: 后端订单服务修改
- **优先级**: P0
- **依赖**: 任务2
- **描述**:
  - 修改订单创建逻辑，处理 items 列表
  - 修改订单查询逻辑，返回 items 明细
- **子任务**:
  - [x] 修改 create_order 方法，创建订单时同时创建 order_items
  - [x] 修改 get_order 方法，返回订单时包含 items
  - [x] 修改 get_orders 方法，列表查询包含 items
  - [x] 添加订单总额计算逻辑

### [x] 任务4: 前端 CreateOrder 组件重构
- **优先级**: P0
- **依赖**: 任务3
- **描述**:
  - 重构创建订单页面，支持多项目选择
  - 实现动态添加/删除项目行
  - 实时计算订单总额
- **子任务**:
  - [x] 修改 formData 结构，使用 items 数组
  - [x] 实现项目行组件（项目选择+数量+单价显示）
  - [x] 实现添加项目功能
  - [x] 实现删除项目功能
  - [x] 实现订单总额实时计算
  - [x] 修改表单提交逻辑

### [x] 任务5: 前端订单详情页修改
- **优先级**: P1
- **依赖**: 任务4
- **描述**:
  - 修改订单详情页，显示项目列表
- **子任务**:
  - [x] 修改 OrderDetail 组件，显示 items 列表
  - [x] 更新样式展示多项目信息

### [x] 任务6: 前端订单列表页修改
- **优先级**: P1
- **依赖**: 任务4
- **描述**:
  - 修改订单列表，显示项目摘要
- **子任务**:
  - [x] 修改 MyOrders 组件，显示项目摘要
  - [x] 修改 OrderPool 组件，显示项目摘要

### [x] 任务7: 数据迁移与兼容性处理
- **优先级**: P1
- **依赖**: 任务1
- **描述**:
  - 处理历史订单数据
  - 确保新旧订单兼容显示
- **子任务**:
  - [x] 编写数据迁移脚本，将历史订单数据迁移到新结构
  - [x] 测试历史订单查询兼容性

## 任务依赖关系

```
任务1 (数据库)
    ↓
任务2 (Schema)
    ↓
任务3 (后端服务)
    ↓
任务4 (前端创建订单)
    ↓
任务5, 任务6 (前端其他页面)

任务7 可与任务2并行
```
