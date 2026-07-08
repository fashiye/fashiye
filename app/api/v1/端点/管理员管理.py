from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel, Field

from app.数据库.会话 import 获取数据库会话
from app.api.依赖.认证 import 获取当前用户, 要求角色
from app.模式.用户 import 用户信息响应
from app.模式.订单 import 管理员零元测试订单创建
from app.服务.订单服务 import 订单服务
from app.模型.用户 import 用户表, 打手表, 管理员表
from app.核心.异常 import 业务逻辑错误
from app.核心.安全 import 生成密码哈希
from app.模型.用户 import 管理员权限表
from app.模型.订单 import 订单表

# ── Pydantic 请求模型（替代裸 dict，提供输入验证） ──────────────
class 更新用户状态请求(BaseModel):
    """管理员更新用户状态的请求体"""
    status: int = Field(..., ge=0, le=1, description="状态: 1-正常, 0-禁用")


class 更新打手状态请求(BaseModel):
    """管理员更新打手状态的请求体"""
    status: Optional[int] = Field(None, ge=0, le=1, description="状态: 1-正常, 0-禁用")
    reviewStatus: Optional[str] = Field(None, description="审核状态: pending/approved/rejected")


class 更新管理员角色请求(BaseModel):
    """超级管理员修改管理员角色的请求体"""
    role: str = Field(..., description="角色: super/operator")


class 创建管理员请求(BaseModel):
    """超级管理员创建管理员账号的请求体"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码（至少6位）")
    permissions: list[str] = Field(default_factory=list, description="权限键列表")


class 更新管理员权限请求(BaseModel):
    """更新管理员权限列表的请求体"""
    permissions: list[str] = Field(..., description="权限键列表")


class 调整打手等级请求(BaseModel):
    """调整打手等级的请求体"""
    level: int = Field(..., ge=1, le=100, description="等级（1-100）")


# 系统预定义合法权限键白名单
合法权限键集合: set[str] = {
    "orders:read", "orders:write", "orders:delete",
    "users:read", "users:write",
    "handlers:read", "handlers:write",
    "admins:read", "admins:write",
    "settings:read", "settings:write",
    "finance:read", "finance:write",
    "system:admin",
}


router = APIRouter()


@router.get("/admin/users")
async def 获取用户列表接口(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, description="按状态筛选: 1=正常 0=禁用"),
    keyword: Optional[str] = Query(None, description="搜索用户名/邮箱/手机号"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员获取用户列表（支持分页、状态筛选和关键词搜索）"""
    查询 = select(用户表)
    if status is not None:
        查询 = 查询.where(用户表.状态 == status)
    if keyword:
        关键词模式 = f"%{keyword}%"
        查询 = 查询.where(
            (用户表.用户名.like(关键词模式)) |
            (用户表.邮箱.like(关键词模式)) |
            (用户表.手机号.like(关键词模式))
        )

    总记录数查询 = select(func.count()).select_from(用户表)
    if status is not None:
        总记录数查询 = 总记录数查询.where(用户表.状态 == status)
    if keyword:
        关键词模式 = f"%{keyword}%"
        总记录数查询 = 总记录数查询.where(
            (用户表.用户名.like(关键词模式)) |
            (用户表.邮箱.like(关键词模式)) |
            (用户表.手机号.like(关键词模式))
        )

    总记录数结果 = await 数据库.execute(总记录数查询)
    总记录数 = 总记录数结果.scalar()

    查询 = 查询.order_by(用户表.id.desc())
    查询 = 查询.offset((page - 1) * size).limit(size)
    结果 = await 数据库.execute(查询)
    用户列表 = 结果.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [用户信息响应(
                id=用户.id,
                username=用户.用户名,
                email=用户.邮箱,
                phone=getattr(用户, '手机号', None),
                avatar=getattr(用户, '头像链接', None),
                status=用户.状态,
                role="user"
            ) for 用户 in 用户列表],
            "total": 总记录数,
            "page": page,
            "pageSize": size
        },
        "message": "获取用户列表成功"
    }


@router.get("/admin/handlers")
async def 获取打手列表接口(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="审核状态: pending/approved/rejected"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员获取打手列表（支持按审核状态筛选）"""
    查询 = select(打手表)
    if status:
        查询 = 查询.where(打手表.审核状态 == status)

    总记录数查询 = select(func.count()).select_from(打手表)
    if status:
        总记录数查询 = 总记录数查询.where(打手表.审核状态 == status)
    总记录数结果 = await 数据库.execute(总记录数查询)
    总记录数 = 总记录数结果.scalar()

    查询 = 查询.order_by(打手表.id.desc())
    查询 = 查询.offset((page - 1) * size).limit(size)
    结果 = await 数据库.execute(查询)
    打手列表 = 结果.scalars().all()

    return {
        "code": 0,
        "data": {
            "items": [{
                "id": 打手.id,
                "username": 打手.用户名,
                "email": 打手.邮箱,
                "phone": getattr(打手, '手机号', None),
                "avatar": getattr(打手, '头像链接', None),
                "status": 打手.状态,
                "level": 打手.等级,
                "reviewStatus": 打手.审核状态,
                "role": "handler"
            } for 打手 in 打手列表],
            "total": 总记录数,
            "page": page,
            "pageSize": size
        },
        "message": "获取打手列表成功"
    }


@router.get("/admin/admins")
async def 获取管理员列表接口(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """超级管理员获取所有管理员账号列表（支持分页）"""
    总记录数查询 = select(func.count()).select_from(管理员表)
    总记录数结果 = await 数据库.execute(总记录数查询)
    总记录数 = 总记录数结果.scalar()

    查询 = select(管理员表).options(selectinload(管理员表.权限列表)).order_by(管理员表.id.desc())
    查询 = 查询.offset((page - 1) * size).limit(size)
    结果 = await 数据库.execute(查询)
    管理员列表 = 结果.scalars().all()

    总页数 = (总记录数 + size - 1) // size

    return {
        "code": 0,
        "data": {
            "items": [{
                "id": 管理员.id,
                "username": 管理员.用户名,
                "email": 管理员.邮箱,
                "status": 管理员.状态,
                "role": 管理员.角色,
                "createdAt": 管理员.创建时间.isoformat() if 管理员.创建时间 else None,
                "permissions": [p.权限键 for p in (管理员.权限列表 or [])]
            } for 管理员 in 管理员列表],
            "total": 总记录数,
            "page": page,
            "pageSize": size,
            "pages": 总页数
        },
        "message": "获取管理员列表成功"
    }


@router.put("/admin/users/{user_id}/status")
async def 更新用户状态接口(
    user_id: int,
    # 传入：含 status（0或1）的请求体
    状态数据: 更新用户状态请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员启用或禁用指定用户账号"""
    用户结果 = await 数据库.execute(select(用户表).where(用户表.id == user_id))
    用户 = 用户结果.scalar_one_or_none()
    if not 用户:
        raise 业务逻辑错误("用户不存在")

    用户.状态 = 状态数据.status

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "用户状态更新成功"}


@router.put("/admin/handlers/{handler_id}/status")
async def 更新打手状态接口(
    handler_id: int,
    # 传入：含 status/ reviewStatus 的请求体
    状态数据: 更新打手状态请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员审核打手或启用/禁用打手账号"""
    打手结果 = await 数据库.execute(select(打手表).where(打手表.id == handler_id))
    打手 = 打手结果.scalar_one_or_none()
    if not 打手:
        raise 业务逻辑错误("打手不存在")

    if 状态数据.status is not None:
        打手.状态 = 状态数据.status
    if 状态数据.reviewStatus is not None:
        if 状态数据.reviewStatus not in ("pending", "approved", "rejected"):
            raise 业务逻辑错误("无效的审核状态")
        打手.审核状态 = 状态数据.reviewStatus

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "打手状态更新成功"}


@router.put("/admin/admins/{admin_id}/role")
async def 更新管理员角色接口(
    admin_id: int,
    # 传入：含 role（super/operator）的请求体
    角色数据: 更新管理员角色请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """超级管理员修改管理员角色"""
    管理员结果 = await 数据库.execute(select(管理员表).where(管理员表.id == admin_id))
    管理员 = 管理员结果.scalar_one_or_none()
    if not 管理员:
        raise 业务逻辑错误("管理员不存在")

    if 角色数据.role not in ("super", "operator"):
        raise 业务逻辑错误("无效的管理员角色")
    管理员.角色 = 角色数据.role

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "管理员角色更新成功"}


@router.delete("/admin/users/{user_id}")
async def 删除用户接口(
    user_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """超级管理员删除用户账号（检查是否有关联订单）"""
    # 调用库函数：查询用户是否存在
    # 传入：user_id(路径参数)
    # 作用：在 users 表中查找指定 ID 的用户记录
    # 传出：用户表 ORM 对象或 None
    用户结果 = await 数据库.execute(select(用户表).where(用户表.id == user_id))
    用户 = 用户结果.scalar_one_or_none()
    if not 用户:
        raise 业务逻辑错误("用户不存在")

    # 检查用户是否有关联订单，防止外键约束错误
    订单查询 = select(func.count(订单表.id)).where(订单表.用户ID == user_id)
    订单结果 = await 数据库.execute(订单查询)
    订单数量 = 订单结果.scalar()
    if 订单数量 and 订单数量 > 0:
        raise 业务逻辑错误(f"该用户存在 {订单数量} 个订单，请先处理关联订单再删除")

    await 数据库.delete(用户)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "用户删除成功"}


@router.post("/admin/orders/test-zero")
async def 创建零元测试订单接口(
    订单数据: 管理员零元测试订单创建,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员创建零元测试订单（跳过支付，直接进入待审核状态）。

    传入：
        订单数据：包含 gameId、accountInfo、items（可选）等字段
        数据库：异步数据库会话
        当前用户信息：管理员身份（super/operator）
    作用：
        创建总金额为 0 的测试订单，直接进入待审核状态，免去支付环节
    传出：
        包含 orderId、orderNo、status 的响应
    """
    当前用户, _ = 当前用户信息
    try:
        订单 = await 订单服务.创建零元测试订单(数据库, 当前用户.id, 订单数据)
        return {
            "code": 0,
            "data": {
                "orderId": 订单.id,
                "orderNo": 订单.订单号,
                "status": 订单.状态,
            },
            "message": "零元测试订单创建成功",
        }
    except Exception as e:
        raise 业务逻辑错误(str(e))


# ─── P1-1: 管理员 CRUD ─────────────────────────────────────────────


@router.post("/admin/admins")
async def 创建管理员接口(
    # 传入：含 username, email, password, permissions（可选权限键列表）的请求体
    创建数据: 创建管理员请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """
    超级管理员创建新的管理员账号。
    传入：创建数据含 username, email, password, permissions（可选权限键列表）
    作用：创建管理员记录，如有 permissions 则同步写入权限表
    传出：创建成功响应含管理员 ID
    """
    from sqlalchemy import func
    # 检查用户名和邮箱是否已存在
    用户名检查 = await 数据库.execute(select(管理员表).where(管理员表.用户名 == 创建数据.username))
    if 用户名检查.scalar_one_or_none():
        raise 业务逻辑错误("用户名已存在")
    邮箱检查 = await 数据库.execute(select(管理员表).where(管理员表.邮箱 == 创建数据.email))
    if 邮箱检查.scalar_one_or_none():
        raise 业务逻辑错误("邮箱已存在")

    新管理员 = 管理员表(
        用户名=创建数据.username,
        邮箱=创建数据.email,
        密码哈希=生成密码哈希(创建数据.password),
        角色="operator",
        状态=0
    )
    数据库.add(新管理员)
    await 数据库.flush()

    # 同步写入权限（校验白名单）
    for 权限键 in 创建数据.permissions:
        if 权限键 not in 合法权限键集合:
            raise 业务逻辑错误(f"非法的权限键: {权限键}")
        数据库.add(管理员权限表(管理员ID=新管理员.id, 权限键=权限键))

    await 数据库.commit()
    await 数据库.refresh(新管理员)
    return {
        "code": 0,
        "data": {"id": 新管理员.id, "username": 新管理员.用户名, "role": 新管理员.角色},
        "message": "管理员创建成功"
    }


@router.delete("/admin/admins/{admin_id}")
async def 删除管理员接口(
    admin_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """
    超级管理员删除指定管理员账号。
    传入：管理员ID（路径参数）
    作用：删除管理员记录（级联删除关联权限）
    传出：无数据
    """
    当前管理员, _ = 当前用户信息
    管理员结果 = await 数据库.execute(select(管理员表).where(管理员表.id == admin_id))
    管理员 = 管理员结果.scalar_one_or_none()
    if not 管理员:
        raise 业务逻辑错误("管理员不存在")
    if 管理员.id == 当前管理员.id or 管理员.角色 == "super":
        raise 业务逻辑错误("不能删除超级管理员或自身")
    await 数据库.delete(管理员)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "管理员已删除"}


@router.get("/admin/admins/{admin_id}/permissions")
async def 获取管理员权限接口(
    admin_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """
    获取指定管理员的权限列表。
    传入：admin_id（路径参数，管理员ID）
    作用：查询 admin_permissions 表获取该管理员所有权限键
    传出：包含 permissions 列表
    """
    权限查询 = select(管理员权限表).where(管理员权限表.管理员ID == admin_id)
    权限结果 = await 数据库.execute(权限查询)
    权限列表 = 权限结果.scalars().all()
    return {
        "code": 0,
        "data": {"permissions": [p.权限键 for p in 权限列表]},
        "message": "获取权限成功"
    }


@router.put("/admin/admins/{admin_id}/permissions")
async def 更新管理员权限接口(
    admin_id: int,
    # 传入：含 permissions（权限键列表）的请求体
    权限数据: 更新管理员权限请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """
    更新指定管理员的权限列表。
    传入：管理员ID（路径参数），权限数据含 permissions（权限键列表）
    作用：先校验权限键合法性，再删除原有权限，再批量插入新权限（同一事务）
    传出：无数据
    """
    管理员结果 = await 数据库.execute(select(管理员表).where(管理员表.id == admin_id))
    管理员 = 管理员结果.scalar_one_or_none()
    if not 管理员:
        raise 业务逻辑错误("管理员不存在")
    if 管理员.角色 == "super":
        raise 业务逻辑错误("超级管理员无需设置权限")

    # 校验所有权限键是否合法
    for 权限键 in 权限数据.permissions:
        if 权限键 not in 合法权限键集合:
            raise 业务逻辑错误(f"非法的权限键: {权限键}")

    try:
        # 删除原有权限
        原权限查询 = select(管理员权限表).where(管理员权限表.管理员ID == admin_id)
        原权限结果 = await 数据库.execute(原权限查询)
        for p in 原权限结果.scalars().all():
            await 数据库.delete(p)

        # 插入新权限
        for 权限键 in 权限数据.permissions:
            数据库.add(管理员权限表(管理员ID=admin_id, 权限键=权限键))

        await 数据库.commit()
    except Exception as e:
        await 数据库.rollback()
        raise 业务逻辑错误(f"权限更新失败: {e}")

    return {"code": 0, "data": None, "message": "权限更新成功"}


# ─── P1-2: 打手管理 ────────────────────────────────────────────────


@router.post("/admin/handlers/{handler_id}/approve")
async def 审核通过打手接口(
    handler_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员审核通过打手申请。
    传入：handler_id（路径参数，打手ID）
    作用：将打手审核状态设为 approved，状态设为正常
    传出：无数据
    """
    打手结果 = await 数据库.execute(select(打手表).where(打手表.id == handler_id))
    打手 = 打手结果.scalar_one_or_none()
    if not 打手:
        raise 业务逻辑错误("打手不存在")
    打手.审核状态 = "approved"
    打手.状态 = 1
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "打手审核通过"}


@router.post("/admin/handlers/{handler_id}/reject")
async def 审核拒绝打手接口(
    handler_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员拒绝打手注册申请。
    传入：handler_id（路径参数，打手ID）
    作用：将打手审核状态设为 rejected，状态设为禁用
    传出：无数据
    """
    打手结果 = await 数据库.execute(select(打手表).where(打手表.id == handler_id))
    打手 = 打手结果.scalar_one_or_none()
    if not 打手:
        raise 业务逻辑错误("打手不存在")
    打手.审核状态 = "rejected"
    打手.状态 = 2
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "打手申请已拒绝"}


@router.put("/admin/handlers/{handler_id}/level")
async def 调整打手等级接口(
    handler_id: int,
    # 传入：含 level（1-100）的请求体
    等级数据: 调整打手等级请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员调整打手等级。
    传入：打手ID（路径参数），等级数据含 level（新等级数值，1-100）
    作用：更新打手等级字段
    传出：无数据
    """
    打手结果 = await 数据库.execute(select(打手表).where(打手表.id == handler_id))
    打手 = 打手结果.scalar_one_or_none()
    if not 打手:
        raise 业务逻辑错误("打手不存在")
    打手.等级 = 等级数据.level
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "打手等级已更新"}
