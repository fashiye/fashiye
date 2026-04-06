# 订单审核功能 - 实现计划

## [x] 任务1: 扩展订单状态枚举
- **Priority**: P0
- **Depends On**: None
- **Description**:
  - 在订单模型中添加 "pending_review" 状态
  - 更新订单状态相关的枚举和映射
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-1.1: 订单创建时默认状态为 "pending_review"
  - `programmatic` TR-1.2: 状态枚举包含 "pending_review"
- **Notes**: 需要更新订单状态的所有使用位置

## [x] 任务2: 修改订单创建逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改 order_service.py 中的 create_order 方法
  - 将新订单的默认状态改为 "pending_review"
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `programmatic` TR-2.1: 新创建的订单状态为 "pending_review"
  - `programmatic` TR-2.2: 订单创建后不显示在订单池
- **Notes**: 保持其他创建逻辑不变

## [x] 任务3: 实现管理员审核 API 端点
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 在 orders.py 中添加管理员审核相关端点
  - 添加 GET /orders/pending-review 端点获取待审核订单
  - 添加 POST /orders/{id}/approve 端点批准订单
  - 添加 POST /orders/{id}/reject 端点拒绝订单
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-3.1: 管理员可以获取待审核订单列表
  - `programmatic` TR-3.2: 批准订单后状态变为 "pending"
  - `programmatic` TR-3.3: 拒绝订单后状态变为 "cancelled"
  - `programmatic` TR-3.4: 非管理员无法访问审核端点
- **Notes**: 需要添加权限验证

## [x] 任务4: 修改订单池查询逻辑
- **Priority**: P0
- **Depends On**: 任务1
- **Description**:
  - 修改 get_order_pool 方法，只返回状态为 "pending" 的订单
  - 确保 "pending_review" 状态的订单不显示在订单池
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic` TR-4.1: 订单池只显示状态为 "pending" 的订单
  - `programmatic` TR-4.2: "pending_review" 状态的订单不显示在订单池
- **Notes**: 保持其他查询逻辑不变

## [x] 任务5: 创建管理员审核页面
- **Priority**: P1
- **Depends On**: 任务3
- **Description**:
  - 创建 AdminOrderReview.jsx 组件
  - 显示待审核订单列表
  - 实现批准和拒绝按钮
  - 集成审核 API 调用
- **Acceptance Criteria Addressed**: AC-2, AC-3, AC-4
- **Test Requirements**:
  - `human-judgment` TR-5.1: 审核页面布局合理，操作清晰
  - `programmatic` TR-5.2: 点击批准/拒绝按钮能正确调用 API
- **Notes**: 只对管理员角色可见

## [x] 任务6: 更新订单列表页面
- **Priority**: P1
- **Depends On**: 任务1
- **Description**:
  - 更新 MyOrders.jsx 以显示 "pending_review" 状态
  - 添加状态文本和样式
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `human-judgment` TR-6.1: 用户订单列表显示 "待审核" 状态
  - `programmatic` TR-6.2: 状态显示正确
- **Notes**: 保持其他功能不变

## [x] 任务7: 测试和验证
- **Priority**: P0
- **Depends On**: 所有任务
- **Description**:
  - 测试完整的审核流程
  - 验证权限控制
  - 测试状态转换
- **Acceptance Criteria Addressed**: 所有 AC
- **Test Requirements**:
  - `programmatic` TR-7.1: 完整流程测试通过
  - `programmatic` TR-7.2: 权限验证正确
  - `human-judgment` TR-7.3: 界面操作流畅
- **Notes**: 测试各种边界情况
