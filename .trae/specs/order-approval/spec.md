# 订单审核功能 - 产品需求文档

## Overview
- **Summary**: 实现订单审核流程，用户发布订单后需要管理员审核批准，审核通过的订单才会显示到订单池供打手接单。
- **Purpose**: 增加平台对订单质量的控制，防止恶意订单或虚假订单的出现。
- **Target Users**: 平台管理员、普通用户、打手

## Goals
- 新增订单审核流程，用户发布的订单默认进入待审核状态
- 管理员可以查看和审核待审核的订单
- 审核通过的订单自动进入订单池
- 审核拒绝的订单通知用户并终止流程
- 保持与现有订单流程的兼容性

## Non-Goals (Out of Scope)
- 不修改现有订单的历史状态
- 不添加批量审核功能
- 不修改订单创建的表单字段

## Background & Context
- 现有订单流程：用户发布订单 → 直接显示到订单池 → 打手接单
- 新订单流程：用户发布订单 → 管理员审核 → 管理员批准 → 订单显示到订单池 → 打手接单
- 订单状态目前包括：pending, accepted, in_progress, review, completed, cancelled, disputed

## Functional Requirements
- **FR-1**: 订单创建后默认状态为 "pending_review"
- **FR-2**: 管理员可以查看所有待审核的订单列表
- **FR-3**: 管理员可以批准或拒绝待审核的订单
- **FR-4**: 批准的订单自动进入 "pending" 状态并显示到订单池
- **FR-5**: 拒绝的订单状态变为 "cancelled" 并通知用户
- **FR-6**: 订单池只显示已批准的订单（状态为 "pending"）

## Non-Functional Requirements
- **NFR-1**: 审核操作必须有管理员权限验证
- **NFR-2**: 审核操作需要记录操作日志
- **NFR-3**: 审核状态变更需要实时反映到前端

## Constraints
- **Technical**: 使用现有的权限系统和状态管理
- **Business**: 审核流程不应影响现有订单的处理

## Assumptions
- 管理员账号已存在且具有相应权限
- 现有订单状态管理系统可以扩展

## Acceptance Criteria

### AC-1: 订单创建后进入待审核状态
- **Given**: 用户创建新订单
- **When**: 订单提交成功
- **Then**: 订单状态为 "pending_review"，不显示在订单池
- **Verification**: `programmatic`

### AC-2: 管理员可以查看待审核订单
- **Given**: 管理员登录系统
- **When**: 访问审核页面
- **Then**: 看到所有状态为 "pending_review" 的订单
- **Verification**: `human-judgment`

### AC-3: 管理员可以批准订单
- **Given**: 管理员在审核页面
- **When**: 点击批准按钮
- **Then**: 订单状态变为 "pending"，显示到订单池
- **Verification**: `programmatic`

### AC-4: 管理员可以拒绝订单
- **Given**: 管理员在审核页面
- **When**: 点击拒绝按钮
- **Then**: 订单状态变为 "cancelled"，从审核列表中消失
- **Verification**: `programmatic`

### AC-5: 订单池只显示已批准的订单
- **Given**: 打手访问订单池
- **When**: 查看订单列表
- **Then**: 只看到状态为 "pending" 的订单，看不到 "pending_review" 的订单
- **Verification**: `programmatic`

## Open Questions
- [ ] 是否需要给用户发送审核结果通知？
- [ ] 审核拒绝时是否需要管理员填写拒绝原因？
