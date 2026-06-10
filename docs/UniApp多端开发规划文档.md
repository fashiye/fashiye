# UniApp 多端开发规划文档

> **目标**：在现有 Web 端（React + Vite）基础上，使用 UniApp 开发原生 APP（iOS + Android），共享后端 API，实现多端并行。
>
> **核心原则**：
> - 后端不动 — 保留所有管理端 API，APP 不暴露管理功能
> - 角色精简 — APP 仅展示「玩家(user)」和「打手(handler)」两种角色
> - 代码复用 — 尽可能复用现有业务逻辑，减少重复开发

---

## 一、架构概览

```
┌──────────────────────────────────────────────────────┐
│                      客户端                           │
│                                                       │
│  ┌──────────────┐    ┌────────────────────────────┐  │
│  │  Web 端       │    │  UniApp APP                │  │
│  │ (React+Vite)  │    │  (iOS + Android)           │  │
│  │  · 全部功能    │    │  · 仅 user + handler      │  │
│  │  · 含管理端    │    │  · 无管理功能              │  │
│  └──────┬───────┘    └──────────┬─────────────────┘  │
│         │                       │                     │
└─────────┼───────────────────────┼─────────────────────┘
          │                       │
          │    HTTP (REST API)    │
          └───────────┬───────────┘
                      │
          ┌───────────┴───────────┐
          │   FastAPI 后端服务      │
          │   (端口 8000)          │
          │                        │
          │   · 认证 /auth         │
          │   · 订单 /orders       │
          │   · 消息 /conversations │
          │   · 游戏 /games        │
          │   · 用户 /users        │
          │   · 管理 /admin/*      │ ← 保留，APP 不调用
          └───────────┬───────────┘
                      │
          ┌───────────┴───────────┐
          │      MySQL 数据库       │
          └───────────────────────┘
```

---

## 二、后端 API 清单（APP 需要调用的接口）

### 2.1 认证模块 `/auth`

| 方法 | 路径 | 说明 | Web 已有 | APP 需要 |
|------|------|------|----------|----------|
| POST | `/auth/send-code` | 发送验证码 | ✅ | ✅ |
| POST | `/auth/register` | 注册 | ✅ | ✅ |
| POST | `/auth/login` | 登录 | ✅ | ✅ |
| POST | `/auth/forgot-password` | 忘记密码 | ✅ | ✅ |
| POST | `/auth/reset-password` | 重置密码 | ✅ | ✅ |
| GET | `/auth/me` | 获取当前用户信息 | ✅ | ✅ |

**注意**：注册/登录时 `role` 参数仅传 `"user"` 或 `"handler"`，不传 `"admin"`。

### 2.2 订单模块 `/orders`

| 方法 | 路径 | 说明 | Web 已有 | APP 需要 |
|------|------|------|----------|----------|
| POST | `/orders` | 创建订单（需 user 角色） | ✅ | ✅ |
| GET | `/orders/pool` | 获取订单池（需 handler 角色） | ✅ | ✅ |
| GET | `/orders/my` | 获取我的订单 | ✅ | ✅ |
| GET | `/orders/{id}` | 获取订单详情 | ✅ | ✅ |
| POST | `/orders/{id}/accept` | 接单（需 handler 角色） | ✅ | ✅ |
| POST | `/orders/{id}/cancel` | 取消订单 | ✅ | ✅ |
| POST | `/orders/{id}/status` | 更新订单状态 | ✅ | ✅ |
| POST | `/orders/{id}/rate` | 评价订单 | ✅ | ✅ |
| GET | `/orders/all` | 全部订单（管理专用） | ✅ | ❌ |
| GET | `/orders/pending-review` | 待审核订单（管理专用） | ✅ | ❌ |
| POST | `/orders/{id}/approve` | 批准订单（管理专用） | ✅ | ❌ |
| POST | `/orders/{id}/reject` | 拒绝订单（管理专用） | ✅ | ❌ |
| DELETE | `/orders/{id}` | 删除订单（管理专用） | ✅ | ❌ |

**订单状态流转**（APP 侧）：
```
创建 → pending(待接单) → accepted(已接单) → in_progress(进行中)
                                                    ↓
                                               review(待验收)
                                                    ↓
                                              completed(已完成)
```
- 用户创建订单 → 直接进入 `pending` 状态（跳过 `pending_review` 审核）
- 打手接单 → `pending` → `accepted`
- 打手开始执行 → `accepted` → `in_progress`
- 打手提交完成 → `in_progress` → `review`
- 用户确认完成 → `review` → `completed`
- 用户/打手取消 → `pending` → `cancelled`

### 2.3 消息模块 `/conversations`

| 方法 | 路径 | 说明 | Web 已有 | APP 需要 |
|------|------|------|----------|----------|
| POST | `/conversations` | 创建会话 | ✅ | ✅ |
| GET | `/conversations` | 获取会话列表 | ✅ | ✅ |
| GET | `/conversations/{id}/messages` | 获取消息列表 | ✅ | ✅ |
| POST | `/conversations/{id}/messages` | 发送消息 | ✅ | ✅ |
| POST | `/conversations/{id}/read` | 标记已读 | ✅ | ✅ |

**请求/响应模型**：

```typescript
// 创建会话请求
interface CreateConversationRequest {
  otherPartyType: "user" | "handler";  // 注意：没有 "admin"
  otherPartyId: number;
  type: "user_handler";
}

// 会话响应
interface ConversationResponse {
  id: number;
  type: string;
  otherPartyId: number;
  otherPartyUsername: string;
  otherPartyAvatar?: string;
  otherPartyRole: string;
  lastMessage?: string;
  lastMessageAt?: string;
  unreadCount: number;
}

// 发送消息请求
interface MessageCreate {
  content: string;
  contentType: "text" | "image" | "file";
  orderId?: number;
}

// 消息响应
interface MessageResponse {
  id: number;
  conversationId: number;
  senderType: string;
  senderId: number;
  content: string;
  contentType: string;
  attachment?: string;
  createdAt: string;
}
```

### 2.4 游戏模块 `/games`

| 方法 | 路径 | 说明 | Web 已有 | APP 需要 |
|------|------|------|----------|----------|
| GET | `/games` | 获取游戏列表 | ✅ | ✅ |
| GET | `/games/{id}` | 获取游戏详情 | ✅ | ✅ |
| GET | `/games/{id}/projects` | 获取游戏的项目列表 | ✅ | ✅ |
| POST | `/games` | 创建游戏（管理专用） | ✅ | ❌ |
| PUT | `/games/{id}` | 更新游戏（管理专用） | ✅ | ❌ |
| DELETE | `/games/{id}` | 删除游戏（管理专用） | ✅ | ❌ |
| POST | `/games/{id}/projects` | 创建项目（管理专用） | ✅ | ❌ |
| DELETE | `/games/{id}/projects/{pid}` | 删除项目（管理专用） | ✅ | ❌ |

### 2.5 用户模块 `/users`

| 方法 | 路径 | 说明 | Web 已有 | APP 需要 |
|------|------|------|----------|----------|
| GET | `/users/available` | 获取可聊天用户列表 | ✅ | ✅ |
| GET | `/users` | 获取全部用户（管理专用） | ✅ | ❌ |
| DELETE | `/users/{id}` | 删除用户（管理专用） | ✅ | ❌ |

---

## 三、UniApp 项目结构与页面映射

### 3.1 项目创建

```bash
# 在项目根目录创建 uni-app 项目
# 建议使用 vue3 + vite + ts 模板
npx degit dcloudio/uni-preset-vue#vite-ts app-mobile
```

建议目录结构：

```
app-mobile/                          # UniApp 项目根目录
├── src/
│   ├── api/                         # API 请求层
│   │   ├── request.ts               # 请求封装（拦截器，Token 管理）
│   │   ├── auth.ts                  # 认证相关 API
│   │   ├── orders.ts                # 订单相关 API
│   │   ├── conversations.ts         # 消息相关 API
│   │   ├── games.ts                 # 游戏相关 API
│   │   └── users.ts                 # 用户相关 API
│   │
│   ├── pages/                       # 页面文件
│   │   ├── login/                   # 登录页
│   │   │   └── index.vue
│   │   ├── register/                # 注册页
│   │   │   └── index.vue
│   │   ├── forgot-password/         # 忘记密码
│   │   │   └── index.vue
│   │   ├── reset-password/          # 重置密码
│   │   │   └── index.vue
│   │   │
│   │   ├── tabs/                    # 底部 Tab 页面
│   │   │   ├── home/               # 首页（角色不同展示不同内容）
│   │   │   │   └── index.vue
│   │   │   ├── orders/             # 订单页
│   │   │   │   └── index.vue
│   │   │   ├── messages/           # 消息列表页
│   │   │   │   └── index.vue
│   │   │   └── profile/            # 个人中心页
│   │   │       └── index.vue
│   │   │
│   │   ├── order-create/            # 创建订单（玩家专用）
│   │   │   └── index.vue
│   │   ├── order-pool/              # 订单池（打手专用）
│   │   │   └── index.vue
│   │   ├── order-detail/            # 订单详情
│   │   │   └── index.vue
│   │   ├── chat/                    # 聊天页
│   │   │   └── index.vue
│   │   └── account/                 # 账户设置
│   │       └── index.vue
│   │
│   ├── components/                  # 公共组件
│   │   ├── OrderCard.vue            # 订单卡片组件
│   │   ├── MessageItem.vue          # 消息项组件
│   │   ├── StatusBadge.vue          # 状态标签组件
│   │   ├── AvatarWithRole.vue       # 头像+角色组件
│   │   ├── GameSelector.vue         # 游戏选择器
│   │   ├── EmptyState.vue           # 空状态组件
│   │   └── LoadingSpinner.vue       # 加载动画组件
│   │
│   ├── stores/                      # 状态管理 (Pinia)
│   │   ├── user.ts                  # 用户状态
│   │   └── order.ts                 # 订单状态
│   │
│   ├── utils/                       # 工具函数
│   │   ├── constants.ts             # 常量（状态映射、角色映射等）
│   │   ├── format.ts                # 格式化（时间、金额）
│   │   └── validate.ts              # 表单验证
│   │
│   └── styles/                      # 公共样式
│       ├── main.scss
│       ├── variables.scss
│       └── theme.scss
│
├── manifest.json                    # UniApp 配置文件
├── pages.json                       # 路由配置
├── uni.scss                         # 全局样式变量
└── vite.config.ts                   # Vite 配置
```

### 3.2 页面映射对照表

| Web 路由 | UniApp 页面 | 角色 | 功能说明 |
|----------|-------------|------|----------|
| `/` (Login) | `/pages/login/index` | 公开 | 登录页，角色选择器（仅 user/handler） |
| `/register` | `/pages/register/index` | 公开 | 注册页，含验证码 |
| `/forgot-password` | `/pages/forgot-password/index` | 公开 | 忘记密码 |
| `/reset-password` | `/pages/reset-password/index` | 公开 | 重置密码 |
| `/user` | `/pages/tabs/home/index` | user | 玩家首页（显示我的订单等） |
| `/handler` | `/pages/tabs/home/index` | handler | 打手首页（显示订单池等） |
| `/user/orders` | `/pages/tabs/orders/index` | user | 我的订单列表 |
| `/handler/orders` | `/pages/tabs/orders/index` | handler | 我的订单列表 |
| `/user/orders/:id` | `/pages/order-detail/index` | user | 订单详情 |
| `/handler/orders/:id` | `/pages/order-detail/index` | handler | 订单详情 |
| `/user/create-order` | `/pages/order-create/index` | user | 创建订单 |
| `/handler/order-pool` | `/pages/order-pool/index` | handler | 订单池 |
| `/user/messages` | `/pages/tabs/messages/index` | all | 消息列表 |
| `/handler/messages` | `/pages/tabs/messages/index` | all | 消息列表 |
| `/user/messages/:id` | `/pages/chat/index` | user | 聊天 |
| `/handler/messages/:id` | `/pages/chat/index` | handler | 聊天 |
| （无） | `/pages/tabs/profile/index` | all | 个人中心（退出登录、账户设置） |
| （无） | `/pages/account/index` | all | 账户管理 |

### 3.3 Tab 导航设计

使用 UniApp 的 `tabBar` 配置底部四个 Tab：

| Tab | 图标 | user 角色含义 | handler 角色含义 |
|-----|------|--------------|-----------------|
| 首页 | home | 我的订单概览 | 订单池概览 |
| 订单 | order | 我的订单列表 | 我的订单列表 |
| 消息 | message | 消息中心 | 消息中心 |
| 我的 | profile | 个人中心 | 个人中心 |

---

## 四、路由与导航设计

### 4.1 pages.json 配置

```json
{
  "pages": [
    {"path": "pages/login/index", "style": {"navigationBarTitleText": "登录"}},
    {"path": "pages/register/index", "style": {"navigationBarTitleText": "注册"}},
    {"path": "pages/forgot-password/index", "style": {"navigationBarTitleText": "忘记密码"}},
    {"path": "pages/reset-password/index", "style": {"navigationBarTitleText": "重置密码"}},
    {"path": "pages/tabs/home/index", "style": {"navigationBarTitleText": "首页"}},
    {"path": "pages/tabs/orders/index", "style": {"navigationBarTitleText": "订单"}},
    {"path": "pages/tabs/messages/index", "style": {"navigationBarTitleText": "消息"}},
    {"path": "pages/tabs/profile/index", "style": {"navigationBarTitleText": "我的"}},
    {"path": "pages/order-create/index", "style": {"navigationBarTitleText": "发布订单"}},
    {"path": "pages/order-pool/index", "style": {"navigationBarTitleText": "订单池"}},
    {"path": "pages/order-detail/index", "style": {"navigationBarTitleText": "订单详情"}},
    {"path": "pages/chat/index", "style": {"navigationBarTitleText": "聊天"}},
    {"path": "pages/account/index", "style": {"navigationBarTitleText": "账户管理"}}
  ],
  "tabBar": {
    "color": "#999",
    "selectedColor": "#6366f1",
    "list": [
      {
        "pagePath": "pages/tabs/home/index",
        "text": "首页",
        "iconPath": "static/tab/home.png",
        "selectedIconPath": "static/tab/home-active.png"
      },
      {
        "pagePath": "pages/tabs/orders/index",
        "text": "订单",
        "iconPath": "static/tab/order.png",
        "selectedIconPath": "static/tab/order-active.png"
      },
      {
        "pagePath": "pages/tabs/messages/index",
        "text": "消息",
        "iconPath": "static/tab/message.png",
        "selectedIconPath": "static/tab/message-active.png"
      },
      {
        "pagePath": "pages/tabs/profile/index",
        "text": "我的",
        "iconPath": "static/tab/profile.png",
        "selectedIconPath": "static/tab/profile-active.png"
      }
    ]
  },
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "游戏代练平台",
    "navigationBarBackgroundColor": "#ffffff",
    "backgroundColor": "#f9fafb"
  }
}
```

### 4.2 角色路由守卫逻辑

UniApp 中没有 React 的 `<ProtectedRoute>`，需要在 APP 启动时校验登录状态，在每个页面 `onLoad` 时检查角色权限。

**核心逻辑**（`api/request.ts` 或 `App.vue` 中实现）：

```typescript
// 1. APP 启动时检查 Token 是否存在
// 2. 请求拦截器自动附加 Token
// 3. 401 响应时自动跳转到登录页
// 4. 页面 onLoad 时检查角色是否匹配

// 角色重定向逻辑
function 获取首页路径(角色: string): string {
  return '/pages/tabs/home/index';  // 统一指向首页，首页内根据角色展示不同内容
}

// 订单列表页（user 和 handler 共用）
function 获取订单列表路径(): string {
  return '/pages/tabs/orders/index';
}
```

---

## 五、API 集成方案

### 5.1 请求封装 (`api/request.ts`)

```typescript
import axios from 'axios';

const 请求实例 = axios.create({
  baseURL: 'http://localhost:8000/api/v1',  // 开发环境
  timeout: 15000,
});

// 请求拦截器 - 自动附加 Token
请求实例.interceptors.request.use(
  (配置) => {
    const 令牌 = uni.getStorageSync('token');
    if (令牌) {
      配置.headers.Authorization = `Bearer ${令牌}`;
    }
    return 配置;
  },
  (错误) => Promise.reject(错误)
);

// 响应拦截器 - 统一错误处理
请求实例.interceptors.response.use(
  (响应) => 响应,
  (错误) => {
    if (错误.response?.status === 401) {
      uni.removeStorageSync('token');
      uni.removeStorageSync('role');
      uni.removeStorageSync('user');
      uni.reLaunch({ url: '/pages/login/index' });
    }
    return Promise.reject(错误);
  }
);

export default 请求实例;
```

### 5.2 API 层示例 (`api/orders.ts`)

```typescript
import request from './request';

export const 订单API = {
  创建订单(数据: {
    gameId: number;
    accountInfo: string;
    requirements?: string;
    items: Array<{ projectId: number; quantity: number }>;
  }) {
    return request.post('/orders', 数据);
  },

  获取订单池(参数?: { game_id?: number; page?: number; size?: number }) {
    return request.get('/orders/pool', { params: 参数 });
  },

  获取我的订单(参数?: { status?: string; page?: number; size?: number }) {
    return request.get('/orders/my', { params: 参数 });
  },

  获取订单详情(订单ID: number) {
    return request.get(`/orders/${订单ID}`);
  },

  接单(订单ID: number) {
    return request.post(`/orders/${订单ID}/accept`);
  },

  取消订单(订单ID: number) {
    return request.post(`/orders/${订单ID}/cancel`);
  },

  更新订单状态(订单ID: number, 数据: { action: string; remark?: string }) {
    return request.post(`/orders/${订单ID}/status`, 数据);
  },

  评价订单(订单ID: number, 数据: { role: string; rating: number; comment?: string }) {
    return request.post(`/orders/${订单ID}/rate`, 数据);
  },
};
```

---

## 六、核心业务模块详细说明

### 6.1 首页（角色区分展示）

**玩家（user）首页**：
- 顶部：用户头像 + 昵称 + 余额
- 快捷入口：发布订单（大按钮）
- 我的订单概览：最近 3 条订单卡片
- 统计信息：总订单数、进行中订单数

**打手（handler）首页**：
- 顶部：打手头像 + 昵称 + 等级/完成率
- 快捷入口：订单池（大按钮）
- 我的订单概览：最近 3 条订单卡片
- 统计信息：总接单数、完成率

### 6.2 创建订单页（玩家专用）

与 Web 端 [CreateOrder.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/CreateOrder.jsx) 功能一致：
1. 选择游戏 → 下拉选择器
2. 选择项目/数量 → 从后端获取项目列表，可添加多行
3. 输入账号信息 → textarea
4. 输入特殊要求 → textarea
5. 显示总金额 → 自动计算
6. 提交按钮 → POST `/orders`

**差异点**：
- 需用 picker 组件代替 select
- 账号信息输入带隐私保护（可切换显示/隐藏）
- 移动端优化：大按钮、触控友好

### 6.3 订单池页（打手专用）

与 Web 端 [OrderPool.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/OrderPool.jsx) 功能一致：
1. 游戏筛选 → picker
2. 订单列表 → 卡片列表（支持下拉刷新 + 上拉加载更多）
3. 接单按钮 → POST `/orders/{id}/accept`

### 6.4 订单列表页（共用）

与 Web 端 [MyOrders.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/MyOrders.jsx) 功能一致：
1. 状态筛选 Tab → 全部/待接单/进行中/已完成/已取消
2. 订单列表 → 卡片列表（下拉刷新 + 上拉加载）
3. 点击进入详情
4. 操作按钮根据角色和状态显示

**打手额外操作**：
- `accepted` → "开始执行"（POST status action=start）
- `in_progress` → "提交完成"（POST status action=submit_complete）

**玩家额外操作**：
- `pending` → "取消订单"
- `review` → "确认完成"（POST status action=confirm_complete）

### 6.5 订单详情页（共用）

与 Web 端 [OrderDetail.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/OrderDetail.jsx) 功能一致：
1. 订单信息（订单号、游戏、金额、状态标签）
2. 项目明细列表
3. 人员信息（发单人/接单人）
4. 账号与备注
5. 时间记录
6. 底部操作按钮（根据状态显示）

### 6.6 消息模块

**消息列表**（与 [MessageList.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/MessageList.jsx) 一致）：
- 会话列表，显示对方头像、昵称、角色标签、最后消息、未读数
- 底部 "+" 按钮 → 调用 `/users/available` 获取可聊天用户列表
- 点击进入聊天

**聊天页**（与 [Chat.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/Chat.jsx) 一致）：
- 顶部：对方昵称 + 角色
- 消息列表：区分自己/对方（气泡样式）
- 底部输入框 + 发送按钮
- 支持 emoji 输入

### 6.7 个人中心（APP 新增）

Web 端没有独立个人中心页，这是 APP 新增页面：
- 用户信息展示（头像、昵称、角色、邮箱）
- 玩家：显示余额
- 打手：显示等级、总订单数、完成率
- 功能入口：账户管理、关于
- 退出登录按钮

### 6.8 账户管理

与 Web 端的「账户管理」卡片功能对应（Web 端当前未实现具体功能）：
- 修改密码（需要旧密码验证）
- 修改个人信息（头像、昵称）

---

## 七、数据模型与枚举值

### 7.1 订单状态映射表

| 状态值 | 显示文本 | 颜色 | 说明 |
|--------|----------|------|------|
| `pending` | 待接单 | `#f59e0b` | 已在订单池中，等待打手接单 |
| `accepted` | 已接单 | `#3b82f6` | 打手已接单，准备开始 |
| `in_progress` | 进行中 | `#6366f1` | 打手正在执行 |
| `review` | 待验收 | `#8b5cf6` | 打手提交完成，等待用户确认 |
| `completed` | 已完成 | `#10b981` | 订单完成 |
| `cancelled` | 已取消 | `#ef4444` | 订单取消 |
| `disputed` | 争议中 | `#f97316` | 产生纠纷 |

### 7.2 角色映射

| 角色值 | 显示文本 | Web 页面路径 |
|--------|----------|-------------|
| `user` | 玩家 | `/{role}/...` |
| `handler` | 打手 | `/{role}/...` |

### 7.3 操作权限对照表

| 操作 | 允许角色 | 前置状态 | 后置状态 | API |
|------|---------|---------|---------|-----|
| 创建订单 | user | - | pending | POST `/orders` |
| 接单 | handler | pending | accepted | POST `/orders/{id}/accept` |
| 开始执行 | handler | accepted | in_progress | POST `/orders/{id}/status` |
| 提交完成 | handler | in_progress | review | POST `/orders/{id}/status` |
| 确认完成 | user | review | completed | POST `/orders/{id}/status` |
| 取消订单 | user | pending | cancelled | POST `/orders/{id}/cancel` |
| 评价 | user/handler | completed | - | POST `/orders/{id}/rate` |

---

## 八、开发阶段建议

### 第一阶段：基础架构搭建（预估 3-5 天）

1. **初始化 UniApp 项目**
   - 使用 `vue3 + vite + ts` 模板创建项目
   - 安装依赖：`axios`, `pinia`, `@uni-helper/xxx`
   - 配置 `manifest.json`（APP 名称、版本、图标等）

2. **API 层搭建**
   - 实现 `api/request.ts`（请求/响应拦截器）
   - 实现所有 API 模块文件

3. **路由与导航配置**
   - 配置 `pages.json`（所有页面路径 + tabBar）
   - 实现登录状态检查

4. **全局样式**
   - 定义 CSS 变量（颜色、字体等，与 Web 端保持一致）
   - 开发 `<StatusBadge>`、`<LoadingSpinner>`、`<EmptyState>` 等公共组件

### 第二阶段：认证模块（预估 2-3 天）

1. **登录页**
   - 角色选择器（玩家/打手）
   - 邮箱 + 密码输入
   - 登录按钮 + 错误处理
   - Token 存储 + 页面跳转

2. **注册页**
   - 角色选择器
   - 用户名 + 邮箱 + 密码 + 手机号
   - 验证码发送（60s 倒计时）
   - 注册成功后跳转

3. **忘记密码/重置密码页**
   - 邮箱输入 + 验证码
   - 新密码输入（含强度校验）
   - 重置成功跳转登录

### 第三阶段：订单模块（预估 5-7 天）

1. **创建订单页**
   - 游戏选择器（从 API 获取）
   - 项目多行输入
   - 账号信息输入
   - 金额计算 + 提交

2. **订单列表页**
   - 状态筛选 Tab
   - 卡片列表 + 下拉刷新/上拉加载
   - 操作按钮（取消/开始/提交完成/确认完成）

3. **订单详情页**
   - 信息展示（订单号、游戏、金额、状态）
   - 项目明细列表
   - 账号信息（可复制）
   - 时间线
   - 底部操作区

4. **订单池页（打手）**
   - 游戏筛选
   - 订单列表
   - 接单操作

### 第四阶段：消息模块（预估 3-4 天）

1. **消息列表页**
   - 会话列表卡片
   - 未读数角标
   - 新建会话（获取可聊天用户）

2. **聊天页**
   - 消息气泡
   - 发送消息
   - 自动滚动到最新

### 第五阶段：个人中心与收尾（预估 2-3 天）

1. **个人中心页**
   - 用户信息展示
   - 角色特有信息（余额/等级）
   - 退出登录

2. **账户管理页**
   - 修改密码
   - 修改个人信息

3. **整体联调与测试**
   - 真机调试
   - 错误边界处理
   - 性能优化

---

## 九、关键注意事项

### 9.1 Token 管理
- UniApp 使用 `uni.getStorageSync`/`uni.setStorageSync` 代替 `localStorage`
- 登录成功后将 `token`、`role`、`user` 信息存入本地存储
- 请求拦截器自动附加 Token
- 401 响应时清除 Token 并跳转登录页

### 9.2 跨域问题
- 开发环境：通过 Vite proxy 或 UniApp 的 `h5.proxy` 配置代理
- 生产环境：后端配置 CORS（已配置 `allow_origins=["*"]`）或使用 nginx 反向代理

### 9.3 Web 端与 APP 端代码共享策略

| 可共享部分 | 不可共享部分 |
|-----------|-------------|
| API 调用参数结构 | UI 组件（Vue vs React） |
| 业务逻辑（状态流转、验证规则） | 路由配置 |
| 数据模型定义 | 样式方案 |
| 常量枚举 | 本地存储 API |
| 请求/响应数据结构 | 导航方式 |

**建议**：将可共享的业务逻辑提取到独立的 npm 包或 mono-repo 的 `shared/` 目录中。

### 9.4 管理功能隐藏

后端管理 API（`database_admin.py`、`orders/all`、`orders/pending-review`、`orders/approve`、`orders/reject`、`games` 的 CRUD 管理接口）在 APP 中**不调用、不展示**，后端代码完全不动。

### 9.5 与 Web 端保持一致的 UI 风格

| 属性 | Web 端值 | APP 推荐值 |
|------|----------|-----------|
| 主色 `--primary` | `#6366f1` | `#6366f1` |
| 成功色 `--success` | `#10b981` | `#10b981` |
| 危险色 `--danger` | `#ef4444` | `#ef4444` |
| 警告色 `--warning` | `#f59e0b` | `#f59e0b` |
| 背景色 | `#f9fafb` | `#f5f5f5` |
| 圆角 | `10px` | `12rpx` |
| 阴影 | `0 1px 3px rgba(0,0,0,0.1)` | 同左 |

### 9.6 测试账号（开发用）

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 玩家 | `user@test.com` | `123456` |
| 打手 | `handler@test.com` | `123456` |

---

## 十、后端关键代码参考

### 10.1 登录接口（需在登录页复现的角色选择逻辑）

参考 [auth.py:login](file:///d:/code/fashiye/app/api/v1/endpoints/auth.py#L149-L211)：
- APP 登录时 `role` 参数只传 `"user"` 或 `"handler"`
- 登录成功返回 `access_token`、`token_type`、`user` 对象
- 将 `user.role` 和 `token` 存入本地存储

### 10.2 注册接口（打手注册差异）

参考 [auth.py:register](file:///d:/code/fashiye/app/api/v1/endpoints/auth.py#L96-L147)：
- 打手注册后 `status=0`（待审批），需管理员在 Web 端审核
- 玩家注册后 `status=1`（正常），可直接使用
- 注册后打手需提示"等待管理员审核"

### 10.3 订单创建（跳过审核）

参考 [order_service.py:create_order](file:///d:/code/fashiye/app/services/order_service.py#L28-L79)：
- 当前订单创建后状态为 `pending_review`
- **注意**：APP 调用时，如果希望跳过审核直接进入订单池，需要后端调整 `status='pending'`（当前不修改后端，保留 `pending_review`，Web 端管理员审核后进入 `pending`）

---

## 附录：Web 端页面文件索引

| Web 文件 | 功能 | 代码行数 |
|----------|------|---------|
| [Login.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/components/Login.jsx) | 登录页（角色选择器） | ~183 行 |
| [Register.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/components/Register.jsx) | 注册页（验证码、密码强度） | ~349 行 |
| [CreateOrder.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/CreateOrder.jsx) | 创建订单（游戏选择、项目列表、金额计算） | ~294 行 |
| [OrderPool.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/OrderPool.jsx) | 订单池（游戏筛选、接单） | ~168 行 |
| [MyOrders.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/MyOrders.jsx) | 我的订单（状态筛选、操作按钮） | ~277 行 |
| [OrderDetail.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/OrderDetail.jsx) | 订单详情（信息展示、操作） | ~268 行 |
| [MessageList.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/MessageList.jsx) | 消息列表（会话列表、新建会话） | ~139 行 |
| [Chat.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/Chat.jsx) | 聊天（消息气泡、发送消息） | ~259 行 |
| [UserDashboard.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/UserDashboard.jsx) | 玩家首页（功能卡片） | ~70 行 |
| [HandlerDashboard.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/pages/HandlerDashboard.jsx) | 打手首页（功能卡片） | ~70 行 |
| [ProtectedRoute.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/components/ProtectedRoute.jsx) | 路由守卫 | ~37 行 |
| [App.jsx](file:///d:/code/fashiye/叶狼游戏代肝/src/App.jsx) | 路由配置（全部路由注册） | ~244 行 |
| [api.js](file:///d:/code/fashiye/叶狼游戏代肝/src/utils/api.js) | API 封装（拦截器、Token） | ~36 行 |
| [index.css](file:///d:/code/fashiye/叶狼游戏代肝/src/index.css) | 全局样式（CSS 变量） | ~91 行 |
