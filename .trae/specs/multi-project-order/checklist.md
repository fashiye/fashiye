# 多项目订单功能验收清单

## 数据库变更验收

- [x] order_items 表已创建
- [x] order_items 表包含正确字段：id, order_id, project_id, quantity, unit_price, total_price, created_at
- [x] OrderItem 模型类已创建
- [x] Order 模型已添加与 OrderItem 的关系

## Schema 变更验收

- [x] OrderItemCreate schema 已创建
- [x] OrderItemResponse schema 已创建
- [x] OrderCreate schema 已修改为支持 items 列表
- [x] OrderResponse schema 已修改为返回 items 列表

## 后端服务验收

- [x] 创建订单 API 能正确处理 items 列表
- [x] 创建订单时正确计算订单总额
- [x] 查询订单 API 返回订单时包含 items 明细
- [x] 列表查询 API 返回订单时包含 items 摘要

## 前端 CreateOrder 验收

- [x] 表单显示项目列表区域
- [x] 可以动态添加项目行
- [x] 可以动态删除项目行（至少保留一行）
- [x] 每行可以选择不同项目
- [x] 每行可以设置不同数量
- [x] 单价根据选择的项目自动显示
- [x] 订单总额实时计算并显示
- [x] 表单提交时正确发送 items 数据

## 前端订单详情验收

- [x] 订单详情页显示项目列表
- [x] 每个项目显示名称、数量、单价、小计
- [x] 显示订单总额

## 前端订单列表验收

- [x] 我的订单列表显示项目摘要
- [x] 订单池列表显示项目摘要
- [x] 项目摘要显示合理（如：排位赛代打 x5, 日常任务 x10）

## 数据兼容性验收

- [x] 历史订单能正常查询和显示
- [x] 新旧订单数据结构兼容

## 业务规则验收

- [x] 订单必须包含至少1个项目
- [x] 每个项目数量 ≥ 1
- [x] 订单总额 = Σ(项目单价 × 数量)
