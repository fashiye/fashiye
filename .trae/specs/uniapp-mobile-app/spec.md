# UniApp 原生 APP 开发 - Product Requirement Document

## Overview
- **Summary**: 使用 UniApp 开发 iOS 和 Android 原生 APP，共享现有 FastAPI 后端，仅保留用户和打手角色功能，管理功能继续在 Web 端使用。
- **Purpose**: 为玩家和打手提供原生移动应用体验，提升使用便利性和用户粘性。
- **Target Users**:
  - 玩家（user）：发布游戏代练订单
  - 打手（handler）：接单并完成代练任务

## Goals
- 使用 UniApp 开发原生 iOS 和 Android 应用
- 共享现有 FastAPI 后端，后端代码不做修改
- 实现玩家和打手的全部核心功能（订单、消息、账户）
- 提供符合移动端设计规范的 UI 体验
- 保持与 Web 端功能一致和数据同步

## Non-Goals (Out of Scope)
- 不实现管理功能（用户管理、订单审核、游戏/项目管理等）
- 不重构后端代码（管理 API 保留，APP 不调用）
- 不开发小程序或 H5 版本（仅原生 iOS/Android）
- 不修改现有 Web 端代码
- 不将项目转换为 mono-repo

## Background & Context
- 已有 Web 端应用：React + Vite，完整功能（含管理端）
- 已有后端：FastAPI + MySQL，完整 API（44 个端点）
- 核心业务流程：玩家下单 → 打手接单 → 完成订单 → 双方评价
- 项目位于：`d:\code\fashiye`

## Functional Requirements
- **FR-1**: 用户认证（登录/注册/忘记密码）
- **FR-2**: 玩家可发布订单（选择游戏/项目、填写账号信息、计算金额）
- **FR-3**: 打手可浏览订单池并接单
- **FR-4**: 用户可查看我的订单列表和订单详情
- **FR-5**: 订单状态流转管理（接单 → 开始执行 → 提交完成 → 确认完成）
- **FR-6**: 用户可查看消息列表和与对方聊天
- **FR-7**: 个人中心（用户信息、退出登录）
- **FR-8**: 订单评价功能

## Non-Functional Requirements
- **NFR-1**: APP 启动时间 < 3 秒
- **NFR-2**: 页面切换流畅，无明显卡顿
- **NFR-3**: API 请求超时时间 15 秒，超时显示友好提示
- **NFR-4**: 适配主流机型（iOS 12+ / Android 7+）
- **NFR-5**: 实现离线状态提示和网络异常处理

## Constraints
- **Technical**:
  - 必须使用 UniApp + Vue3 + TypeScript + Vite
  - 后端必须复用现有 FastAPI (端口 8000)
  - 数据库必须复用现有 MySQL 数据库
  - 前端代码独立存放于 `app-mobile/` 目录
- **Business**:
  - 管理功能必须保留在 Web 端，APP 不展示任何管理入口
  - 与 Web 端数据完全同步
- **Dependencies**:
  - 依赖现有后端 API（`/api/v1/*`）
  - 依赖现有的 MySQL 数据库和数据结构

## Assumptions
- 后端服务运行在 `http://localhost:8000`（开发环境）
- 现有的 Web 端账号密码可以在 APP 端使用
- 打手账号需要管理员在 Web 端审核通过后才能登录
- 用户在 APP 端发布的订单需要管理员在 Web 端审核后进入订单池（保持现有流程）

## Acceptance Criteria

### AC-1: 用户登录
- **Given**: 用户已注册且账号状态正常
- **When**: 用户在登录页选择角色（玩家/打手），输入正确邮箱和密码并点击登录
- **Then**: APP 从后端获取 Token，存储到本地，跳转到首页
- **Verification**: `programmatic`

### AC-2: 用户注册
- **Given**: 用户没有账号
- **When**: 用户在注册页填写信息、获取并输入正确验证码，点击注册
- **Then**: 用户注册成功，登录状态保持，跳转到首页（玩家）或提示等待审核（打手）
- **Verification**: `programmatic`

### AC-3: 玩家发布订单
- **Given**: 玩家已登录
- **When**: 玩家在发布订单页选择游戏、选择项目/填写数量、输入账号信息、填写要求并提交
- **Then**: 订单创建成功（状态 pending_review），跳转到订单详情页
- **Verification**: `programmatic`

### AC-4: 打手浏览订单池
- **Given**: 打手已登录
- **When**: 打手进入订单池页，可选择游戏筛选，浏览订单列表
- **Then**: 从后端获取订单池列表并正确展示
- **Verification**: `programmatic`

### AC-5: 打手接单
- **Given**: 打手已登录且订单处于 pending 状态
- **When**: 打手点击订单卡片的接单按钮，确认后提交
- **Then**: 订单状态变为 accepted，进入打手的我的订单列表
- **Verification**: `programmatic`

### AC-6: 查看订单详情
- **Given**: 用户已登录且订单属于该用户
- **When**: 用户从订单列表点击订单进入详情页
- **Then**: 正确显示订单信息、项目明细、账号信息、人员信息、时间记录、操作按钮
- **Verification**: `human-judgment`

### AC-7: 订单状态流转
- **Given**: 用户已登录且订单处于正确的前置状态
- **When**: 用户点击对应操作（开始执行/提交完成/确认完成/取消订单）
- **Then**: 订单状态正确更新，UI 同步刷新
- **Verification**: `programmatic`

### AC-8: 消息聊天
- **Given**: 用户已登录且存在会话
- **When**: 用户进入消息列表，选择会话进入聊天页，发送消息
- **Then**: 消息正确发送并实时展示（无需 WebSocket，轮询或刷新查看）
- **Verification**: `human-judgment`

### AC-9: 底部 Tab 导航
- **Given**: 用户已登录
- **When**: 用户在 APP 内操作
- **Then**: 显示底部四个 Tab：首页/订单/消息/我的，点击可切换
- **Verification**: `human-judgment`

### AC-10: 个人中心
- **Given**: 用户已登录
- **When**: 用户进入我的 Tab
- **Then**: 正确显示用户信息（头像、昵称、角色、玩家显示余额/打手显示等级），提供退出登录功能
- **Verification**: `human-judgment`

## Open Questions
- [ ] 订单创建时是否需要修改后端，让 APP 发布的订单直接进入 pending 状态（跳过审核）？（当前文档：保留现有流程，管理员审核后进入订单池）
- [ ] 是否需要在 APP 端实现修改密码功能？
