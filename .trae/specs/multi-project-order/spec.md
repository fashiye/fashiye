# 多项目订单功能设计规格

## 背景与问题

当前订单系统存在以下问题：
- 用户只能选择一个项目并设置数量
- 实际场景中，用户可能需要多个不同项目，每个项目有不同数量（例如：排位赛代打5局 + 日常任务代做10个）
- 现有设计无法满足这种复杂需求

## 目标

重新设计订单创建流程，支持用户在一个订单中选择多个项目，每个项目可独立设置数量。

## 方案设计

### 方案对比

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A. 购物车模式 | 类似电商购物车，先添加项目到购物车，再统一结算生成订单 | 用户体验好，可随时调整 | 实现复杂，需要购物车表 |
| B. 多项目表单 | 订单表单中支持动态添加多个项目行 | 实现简单，直接明了 | 表单可能较长 |
| C. 订单拆分 | 用户选择多个项目时，后端拆分成多个独立订单 | 简单，复用现有逻辑 | 用户看到多个订单，体验差 |

**选定方案：B（多项目表单）**
- 在现有表单基础上增加项目列表
- 每行一个项目+数量，可动态添加/删除
- 保持实现简单的同时满足需求

## 数据模型变更

### OrderCreate Schema 修改

```python
class OrderItem(BaseModel):
    """订单项目"""
    projectId: int
    quantity: int = Field(..., ge=1)
    unitPrice: Decimal  # 项目单价（后端根据projectId查询填充）

class OrderCreate(BaseModel):
    gameId: int
    accountInfo: str
    requirements: Optional[str] = None
    items: List[OrderItem]  # 订单项目列表（至少1项）
    # 移除：type, projectId, quantity, customName, customDescription, customPrice
```

### 数据库变更

**新增表：order_items**
```sql
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    project_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**orders表调整**
- 移除：project_id, quantity, unit_price, custom_name, custom_description, custom_price, type
- 保留：total_amount（订单总金额，由order_items汇总计算）

## API 变更

### POST /orders

**请求体变更：**
```json
{
  "gameId": 1,
  "accountInfo": "账号: xxx, 密码: xxx",
  "requirements": "特殊要求",
  "items": [
    {"projectId": 1, "quantity": 5},
    {"projectId": 2, "quantity": 10}
  ]
}
```

**响应保持现有格式**

### GET /orders/{id}

**响应增加items字段：**
```json
{
  "id": 1,
  "orderNo": "ORD20240101123456",
  "items": [
    {"projectId": 1, "projectName": "排位赛代打", "quantity": 5, "unitPrice": 10.00, "totalPrice": 50.00},
    {"projectId": 2, "projectName": "日常任务代做", "quantity": 10, "unitPrice": 5.00, "totalPrice": 50.00}
  ],
  "totalAmount": 100.00
}
```

## 前端界面设计

### 创建订单页面

```
┌─────────────────────────────────────────┐
│ 发布订单                           返回  │
├─────────────────────────────────────────┤
│ 基本信息                                │
│ ┌─────────────────────────────────────┐ │
│ │ 选择游戏 *  [游戏下拉框 ▼]          │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 项目列表 *                              │
│ ┌─────────────────────────────────────┐ │
│ │ 项目                    数量   单价 │ │
│ │ [排位赛代打    ▼]  [ 5 ]  ¥10.00  │ │
│ │ [日常任务代做  ▼]  [10 ]  ¥5.00   │ │
│ │ [请选择项目    ▼]  [ 1 ]  ¥0.00   │ │
│ │                                     │ │
│ │ + 添加项目                          │ │
│ └─────────────────────────────────────┘ │
│ 订单总额: ¥100.00                       │
│                                         │
│ 账号信息 *                              │
│ ┌─────────────────────────────────────┐ │
│ │ [账号信息输入框...                ] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ 其他要求                                │
│ ┌─────────────────────────────────────┐ │
│ │ [特殊要求输入框...                ] │ │
│ └─────────────────────────────────────┘ │
│                                         │
│          [取消]    [发布订单]           │
└─────────────────────────────────────────┘
```

**交互说明：**
- 选择游戏后，项目下拉框加载该游戏的项目列表
- 点击"+ 添加项目"增加一行项目选择
- 每行可选择不同项目，设置不同数量
- 单价自动根据项目显示，不可编辑
- 订单总额实时计算显示
- 至少保留一行，最后一行不可删除

## 业务规则

1. **最少项目数**：订单必须包含至少1个项目
2. **项目唯一性**：同一项目不能重复选择（或重复选择时数量累加）
3. **数量限制**：每个项目数量 ≥ 1
4. **总额计算**：订单总额 = Σ(项目单价 × 数量)
5. **自定义项目**：如需自定义项目，建议管理员先在后台添加为正式项目

## 兼容性考虑

**现有订单处理：**
- 历史订单保持现有数据结构不变
- 查询时通过LEFT JOIN order_items，若无子项则按旧逻辑显示
- 新订单统一使用新结构存储

## 影响范围

- 前端：CreateOrder.jsx, OrderDetail.jsx, MyOrders.jsx, OrderPool.jsx
- 后端：order schema, order service, order endpoints
- 数据库：新增order_items表，orders表字段调整
