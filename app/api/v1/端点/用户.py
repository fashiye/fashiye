from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List

from app.数据库.会话 import 获取数据库会话
from app.api.依赖.认证 import 获取当前用户, 要求角色
from app.模式.用户 import 用户信息响应
from app.模型.用户 import 用户表, 打手表, 管理员表
from app.核心.异常 import 业务逻辑错误

router = APIRouter()


@router.get("/users/available")
async def 获取可聊天用户接口(
    角色过滤: Optional[str] = Query(None, description="筛选角色: user/handler"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取当前用户可以发起聊天的用户列表"""
    当前用户, 当前角色 = 当前用户信息

    可用列表: List[dict] = []

    if 当前角色 == "user":
        # 用户可以看到所有打手
        打手查询 = select(打手表).where(打手表.状态 == 1, 打手表.审核状态 == "approved")
        打手结果 = await 数据库.execute(打手查询)
        打手列表 = 打手结果.scalars().all()
        for 打手 in 打手列表:
            可用列表.append({
                "id": 打手.id,
                "username": 打手.用户名,
                "role": "handler",
            })
    elif 当前角色 == "handler":
        用户查询 = select(用户表).where(用户表.状态 == 1)
        用户结果 = await 数据库.execute(用户查询)
        用户列表 = 用户结果.scalars().all()
        for 用户 in 用户列表:
            可用列表.append({
                "id": 用户.id,
                "username": 用户.用户名,
                "role": "user",
            })
    elif 当前角色 in ["super", "operator"]:
        # 管理员可以看到所有用户和打手
        用户查询 = select(用户表).where(用户表.状态 == 1)
        用户结果 = await 数据库.execute(用户查询)
        用户列表 = 用户结果.scalars().all()
        for 用户 in 用户列表:
            可用列表.append({
                "id": 用户.id,
                "username": 用户.用户名,
                "role": "user",
            })
        打手查询 = select(打手表).where(打手表.状态 == 1)
        打手结果 = await 数据库.execute(打手查询)
        打手列表 = 打手结果.scalars().all()
        for 打手 in 打手列表:
            可用列表.append({
                "id": 打手.id,
                "username": 打手.用户名,
                "role": "handler",
            })

    if 角色过滤:
        可用列表 = [u for u in 可用列表 if u["role"] == 角色过滤]

    return {"code": 0, "data": 可用列表, "message": "获取成功"}


@router.get("/users/me")
async def 获取当前用户信息接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取当前登录用户的详细信息（自动适配用户/打手/管理员角色）"""
    当前用户, 当前角色 = 当前用户信息

    响应数据 = {
        "id": 当前用户.id,
        "username": 当前用户.用户名,
        "email": 当前用户.邮箱,
        "phone": getattr(当前用户, '手机号', None),
        "avatar": getattr(当前用户, '头像链接', None),
        "status": 当前用户.状态,
        "role": 当前角色
    }

    if 当前角色 == "user":
        响应数据["totalOrders"] = 0
        响应数据["balance"] = 0
    elif 当前角色 == "handler":
        打手结果 = await 数据库.execute(
            select(打手表).where(打手表.id == 当前用户.id)
        )
        打手 = 打手结果.scalar_one_or_none()
        响应数据["level"] = 打手.等级 if 打手 else None
        响应数据["completionRate"] = None
        响应数据["totalOrders"] = 0

    return {"code": 0, "data": 响应数据, "message": "获取用户信息成功"}


@router.put("/users/profile")
async def 更新个人资料接口(
    资料数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """更新当前用户的个人资料（用户名、手机号、头像等）"""
    当前用户, 当前角色 = 当前用户信息

    if "username" in 资料数据:
        当前用户.用户名 = 资料数据["username"]
    if "phone" in 资料数据:
        当前用户.手机号 = 资料数据["phone"]
    if "avatar" in 资料数据:
        当前用户.头像链接 = 资料数据["avatar"]

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "资料更新成功"}


@router.post("/users/change-password")
async def 修改密码接口(
    密码数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """修改当前用户密码（需提供旧密码验证）"""
    当前用户, 当前角色 = 当前用户信息

    from app.核心.安全 import 验证密码明文, 生成密码哈希

    旧密码 = 密码数据.get("oldPassword")
    新密码 = 密码数据.get("newPassword")

    if not 旧密码 or not 新密码:
        raise 业务逻辑错误("请提供旧密码和新密码")

    if not 验证密码明文(旧密码, 当前用户.密码哈希):
        raise 业务逻辑错误("旧密码不正确")

    if len(新密码) < 6:
        raise 业务逻辑错误("新密码长度不能少于6位")

    当前用户.密码哈希 = 生成密码哈希(新密码)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "密码修改成功"}


@router.get("/users/{user_id}")
async def 获取指定用户信息接口(
    user_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取指定用户的信息（管理员权限）"""
    当前用户, 当前角色 = 当前用户信息

    用户结果 = await 数据库.execute(select(用户表).where(用户表.id == user_id))
    用户 = 用户结果.scalar_one_or_none()
    if 用户:
        return {
            "code": 0,
            "data": {
                "id": 用户.id,
                "username": 用户.用户名,
                "email": 用户.邮箱,
                "phone": getattr(用户, '手机号', None),
                "avatar": getattr(用户, '头像链接', None),
                "status": 用户.状态,
                "role": "user"
            },
            "message": "获取用户信息成功"
        }

    打手结果 = await 数据库.execute(select(打手表).where(打手表.id == user_id))
    打手 = 打手结果.scalar_one_or_none()
    if 打手:
        return {
            "code": 0,
            "data": {
                "id": 打手.id,
                "username": 打手.用户名,
                "email": 打手.邮箱,
                "phone": getattr(打手, '手机号', None),
                "avatar": getattr(打手, '头像链接', None),
                "status": 打手.状态,
                "role": "handler",
                "level": 打手.等级
            },
            "message": "获取用户信息成功"
        }

    raise HTTPException(status_code=404, detail="用户不存在")


@router.get("/handler/{handler_id}/profile")
async def 获取打手公开资料接口(
    handler_id: int,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """获取打手的公开资料（无需登录）"""
    打手结果 = await 数据库.execute(
        select(打手表).where(打手表.id == handler_id)
    )
    打手 = 打手结果.scalar_one_or_none()
    if not 打手:
        raise HTTPException(status_code=404, detail="打手不存在")

    return {
        "code": 0,
        "data": {
            "id": 打手.id,
            "username": 打手.用户名,
            "avatar": getattr(打手, '头像链接', None),
            "level": 打手.等级,
            "completionRate": None,
            "totalOrders": 0
        },
        "message": "获取打手信息成功"
    }
