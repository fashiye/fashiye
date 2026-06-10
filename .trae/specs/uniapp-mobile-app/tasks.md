# UniApp 原生 APP 开发 - The Implementation Plan (Decomposed and Prioritized Task List)

## [x] Task 1: 初始化 UniApp 项目
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 使用 `dcloudio/uni-preset-vue#vite-ts` 模板初始化项目
  - 项目根目录命名为 `app-mobile/`
  - 安装必需依赖：`axios`, `pinia`（可选，但推荐）
  - 配置 `manifest.json`（APP 名称、版本、图标、权限）
  - 配置 `pages.json`（基础路由框架，不含完整页面）
  - 配置 `vite.config.ts`（代理后端请求）
- **Acceptance Criteria Addressed**: N/A（基础设施）
- **Test Requirements**:
  - `human-judgement` TR-1.1: 项目能在 H5 和小程序模拟器（或真机）正常运行
  - `programmatic` TR-1.2: 基本的编译过程无错误
- **Notes**: 参考官方文档 https://uniapp.dcloud.net.cn/quickstart-cli.html

## [x] Task 2: 搭建 API 请求层与 Token 管理
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 创建 `src/api/request.ts`：实现 axios 实例、请求/响应拦截器、Token 自动附加
  - 使用 `uni.getStorageSync`/`uni.setStorageSync` 代替 localStorage
  - 创建各模块 API 文件：`auth.ts`、`orders.ts`、`conversations.ts`、`games.ts`、`users.ts`
  - 实现统一的错误处理（401 自动跳转登录）
- **Acceptance Criteria Addressed**: N/A（基础设施）
- **Test Requirements**:
  - `programmatic` TR-2.1: 请求拦截器能正确附加 Token
  - `programmatic` TR-2.2: 响应拦截器能正确处理 401 并跳转登录
  - `programmatic` TR-2.3: API 请求能正确代理到后端 http://localhost:8000

## [x] Task 3: 实现登录与注册页面
- **Priority**: P0
- **Depends On**: Task 2
- **Description**:
  - 创建登录页 `src/pages/login/index.vue`（角色选择器：仅玩家/打手）
  - 创建注册页 `src/pages/register/index.vue`（含邮箱验证码、密码强度校验）
  - 创建忘记密码页 `src/pages/forgot-password/index.vue`
  - 创建重置密码页 `src/pages/reset-password/index.vue`
  - 更新 `pages.json` 加入这些路由
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 登录成功后 Token 存储到本地
  - `programmatic` TR-3.2: 登录成功后跳转到首页
  - `human-judgement` TR-3.3: 注册页有 60s 验证码倒计时
  - `human-judgement` TR-3.4: 打手注册成功后提示"等待管理员审核"

## [x] Task 4: 实现底部 Tab 导航与首页
- **Priority**: P0
- **Depends On**: Task 3
- **Description**:
  - 配置 `pages.json` 的 `tabBar`（首页/订单/消息/我的）
  - 创建首页 `src/pages/tabs/home/index.vue`（根据角色动态展示不同内容）
  - 创建我的页面 `src/pages/tabs/profile/index.vue`（用户信息 + 退出登录）
  - 实现路由守卫逻辑：登录校验
- **Acceptance Criteria Addressed**: AC-9, AC-10
- **Test Requirements**:
  - `human-judgement` TR-4.1: 底部四个 Tab 可正常切换
  - `human-judgement` TR-4.2: 玩家首页和打手首页展示内容不同
  - `human-judgement` TR-4.3: 点击退出登录后清除 Token 并跳转到登录页

## [x] Task 5: 实现订单列表与详情页
- **Priority**: P0
- **Depends On**: Task 4
- **Description**:
  - 创建订单列表页 `src/pages/tabs/orders/index.vue`（状态筛选 Tab，下拉刷新）
  - 创建订单详情页 `src/pages/order-detail/index.vue`
  - 创建订单卡片组件 `src/components/OrderCard.vue`
  - 创建状态标签组件 `src/components/StatusBadge.vue`
  - 实现取消订单、确认完成等操作
- **Acceptance Criteria Addressed**: AC-6, AC-7
- **Test Requirements**:
  - `programmatic` TR-5.1: 调用 `/orders/my` 能正确获取订单列表
  - `programmatic` TR-5.2: 调用 `/orders/{id}` 能正确获取订单详情
  - `human-judgement` TR-5.3: 订单列表和详情页 UI 符合移动端设计
  - `human-judgement` TR-5.4: 操作按钮根据角色和状态正确显示

## [x] Task 6: 实现玩家创建订单页
- **Priority**: P0
- **Depends On**: Task 5
- **Description**:
  - 创建创建订单页 `src/pages/order-create/index.vue`
  - 实现游戏选择器（从 `/games` 获取）
  - 实现项目多行输入（从 `/games/{id}/projects` 获取项目列表）
  - 实现账号信息输入区、要求输入区、总金额自动计算
  - 实现表单验证
- **Acceptance Criteria Addressed**: AC-3
- **Test Requirements**:
  - `programmatic` TR-6.1: 调用 `/games` 能正确获取游戏列表
  - `programmatic` TR-6.2: 调用 `/orders` POST 请求能正确创建订单
  - `human-judgement` TR-6.3: 金额自动计算正确
  - `human-judgement` TR-6.4: 表单验证（必填项）正确

## [x] Task 7: 实现打手订单池页
- **Priority**: P0
- **Depends On**: Task 6
- **Description**:
  - 创建订单池页 `src/pages/order-pool/index.vue`
  - 实现游戏筛选
  - 实现订单列表展示与接单功能
  - 实现下拉刷新与上拉加载更多
- **Acceptance Criteria Addressed**: AC-4, AC-5
- **Test Requirements**:
  - `programmatic` TR-7.1: 调用 `/orders/pool` 能正确获取订单池
  - `programmatic` TR-7.2: 调用 `/orders/{id}/accept` 能成功接单
  - `human-judgement` TR-7.3: 订单池 UI 符合移动端设计

## [x] Task 8: 实现消息模块
- **Priority**: P1
- **Depends On**: Task 7
- **Description**:
  - 创建消息列表页 `src/pages/tabs/messages/index.vue`
  - 创建聊天页 `src/pages/chat/index.vue`
  - 创建消息项组件 `src/components/MessageItem.vue`
  - 实现会话列表、未读数展示、发送消息
  - 实现新建会话（调用 `/users/available` 获取可聊天用户）
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `programmatic` TR-8.1: 调用 `/conversations` 能正确获取会话列表
  - `programmatic` TR-8.2: 调用 `/conversations/{id}/messages` 能正确获取消息列表
  - `programmatic` TR-8.3: 调用 `/conversations/{id}/messages` POST 能发送消息
  - `human-judgement` TR-8.4: 聊天页 UI 符合移动端聊天习惯（气泡样式、时间显示）

## [x] Task 9: 实现订单评价功能
- **Priority**: P1
- **Depends On**: Task 8
- **Description**:
  - 在订单详情页中添加评价入口（仅在订单 completed 状态时显示）
  - 实现评价弹窗（星级评分 + 评论输入）
  - 调用 `/orders/{id}/rate` 提交评价
- **Acceptance Criteria Addressed**: FR-8
- **Test Requirements**:
  - `programmatic` TR-9.1: 调用 `/orders/{id}/rate` 能成功提交评价
  - `human-judgement` TR-9.2: 评价弹窗 UI 友好，操作流畅

## [x] Task 10: 实现账户管理页
- **Priority**: P2
- **Depends On**: Task 9
- **Description**:
  - 创建账户管理页 `src/pages/account/index.vue`
  - 实现修改密码功能（可选，根据实际需求）
  - 实现修改个人信息（头像、昵称）功能（可选）
- **Acceptance Criteria Addressed**: N/A（额外功能）
- **Test Requirements**:
  - `human-judgement` TR-10.1: 页面 UI 一致
- **Notes**: 此功能优先级较低，可先做框架，具体功能后续补充

## [x] Task 11: 整体联调、测试与优化
- **Priority**: P1
- **Depends On**: Task 10
- **Description**:
  - 在 iOS 和 Android 真机上测试所有功能
  - 修复发现的 bug
  - 优化加载状态、错误状态、空状态展示
  - 优化性能（列表流畅度、启动时间）
  - 添加必要的 Loading/Empty 组件
- **Acceptance Criteria Addressed**: NFR-1, NFR-2, NFR-3, NFR-4, NFR-5
- **Test Requirements**:
  - `human-judgement` TR-11.1: 所有功能在真机上正常运行
  - `human-judgement` TR-11.2: 所有错误和异常状态有友好提示
