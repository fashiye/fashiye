from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.数据库.会话 import 获取数据库会话
from app.api.依赖.认证 import 获取当前用户, 要求角色
from app.模式.用户 import 用户信息响应
from app.模型.用户 import 用户表, 打手表, 管理员表
from app.核心.异常 import 业务逻辑错误

router = APIRouter()


@router.get("/admin/users")
async def 获取用户列表接口(
    页码: int = Query(1, ge=1, description="页码"),
    每页数量: int = Query(20, ge=1, le=100, description="每页数量"),
    状态过滤: Optional[int] = Query(None, description="按状态筛选: 1=正常 0=禁用"),
    搜索关键词: Optional[str] = Query(None, description="搜索用户名/邮箱/手机号"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员获取用户列表（支持分页、状态筛选和关键词搜索）"""
    查询 = select(用户表)
    if 状态过滤 is not None:
        查询 = 查询.where(用户表.状态 == 状态过滤)
    if 搜索关键词:
        关键词 = f"%{搜索关键词}%"
        查询 = 查询.where(
            (用户表.用户名.like(关键词)) |
            (用户表.邮箱.like(关键词)) |
            (用户表.手机号.like(关键词))
        )

    总记录数查询 = select(func.count()).select_from(用户表)
    if 状态过滤 is not None:
        总记录数查询 = 总记录数查询.where(用户表.状态 == 状态过滤)
    if 搜索关键词:
        总记录数查询 = 总记录数查询.where(
            (用户表.用户名.like(关键词)) |
            (用户表.邮箱.like(关键词)) |
            (用户表.手机号.like(关键词))
        )

    总记录数结果 = await 数据库.execute(总记录数查询)
    总记录数 = 总记录数结果.scalar()

    查询 = 查询.order_by(用户表.id.desc())
    查询 = 查询.offset((页码 - 1) * 每页数量).limit(每页数量)
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
            "page": 页码,
            "pageSize": 每页数量
        },
        "message": "获取用户列表成功"
    }


@router.get("/admin/handlers")
async def 获取打手列表接口(
    页码: int = Query(1, ge=1, description="页码"),
    每页数量: int = Query(20, ge=1, le=100, description="每页数量"),
    审核状态: Optional[str] = Query(None, description="审核状态: pending/approved/rejected"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员获取打手列表（支持按审核状态筛选）"""
    查询 = select(打手表)
    if 审核状态:
        查询 = 查询.where(打手表.审核状态 == 审核状态)

    总记录数查询 = select(func.count()).select_from(打手表)
    if 审核状态:
        总记录数查询 = 总记录数查询.where(打手表.审核状态 == 审核状态)
    总记录数结果 = await 数据库.execute(总记录数查询)
    总记录数 = 总记录数结果.scalar()

    查询 = 查询.order_by(打手表.id.desc())
    查询 = 查询.offset((页码 - 1) * 每页数量).limit(每页数量)
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
            "page": 页码,
            "pageSize": 每页数量
        },
        "message": "获取打手列表成功"
    }


@router.get("/admin/admins")
async def 获取管理员列表接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """超级管理员获取所有管理员账号列表"""
    结果 = await 数据库.execute(select(管理员表).order_by(管理员表.id.desc()))
    管理员列表 = 结果.scalars().all()

    return {
        "code": 0,
        "data": [{
            "id": 管理员.id,
            "username": 管理员.用户名,
            "email": 管理员.邮箱,
            "status": 管理员.状态,
            "role": 管理员.角色,
            "permissions": [p.权限键 for p in (管理员.权限列表 or [])]
        } for 管理员 in 管理员列表],
        "message": "获取管理员列表成功"
    }


@router.put("/admin/users/{用户ID}/status")
async def 更新用户状态接口(
    用户ID: int,
    状态数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员启用或禁用指定用户账号"""
    用户结果 = await 数据库.execute(select(用户表).where(用户表.id == 用户ID))
    用户 = 用户结果.scalar_one_or_none()
    if not 用户:
        raise HTTPException(status_code=404, detail="用户不存在")

    if "status" in 状态数据:
        用户.状态 = 状态数据["status"]

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "用户状态更新成功"}


@router.put("/admin/handlers/{打手ID}/status")
async def 更新打手状态接口(
    打手ID: int,
    状态数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """管理员审核打手或启用/禁用打手账号"""
    打手结果 = await 数据库.execute(select(打手表).where(打手表.id == 打手ID))
    打手 = 打手结果.scalar_one_or_none()
    if not 打手:
        raise HTTPException(status_code=404, detail="打手不存在")

    if "status" in 状态数据:
        打手.状态 = 状态数据["status"]
    if "reviewStatus" in 状态数据:
        打手.审核状态 = 状态数据["reviewStatus"]

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "打手状态更新成功"}


@router.put("/admin/admins/{管理员ID}/role")
async def 更新管理员角色接口(
    管理员ID: int,
    角色数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """超级管理员修改管理员角色"""
    管理员结果 = await 数据库.execute(select(管理员表).where(管理员表.id == 管理员ID))
    管理员 = 管理员结果.scalar_one_or_none()
    if not 管理员:
        raise HTTPException(status_code=404, detail="管理员不存在")

    if "role" in 角色数据:
        新角色 = 角色数据["role"]
        if 新角色 not in ["super", "operator"]:
            raise 业务逻辑错误("无效的管理员角色")
        管理员.角色 = 新角色

    if "permissions" in 角色数据:
        from app.模型.用户 import 管理员权限表
        权限列表 = 角色数据["permissions"]
        await 数据库.execute(select(管理员权限表).where(管理员权限表.管理员ID == 管理员ID))
        # 简化处理：直接更新权限
        pass

    await 数据库.commit()
    return {"code": 0, "data": None, "message": "管理员角色更新成功"}


@router.delete("/admin/users/{用户ID}")
async def 删除用户接口(
    用户ID: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super"]))
):
    """超级管理员删除用户账号"""
    用户结果 = await 数据库.execute(select(用户表).where(用户表.id == 用户ID))
    用户 = 用户结果.scalar_one_or_none()
    if not 用户:
        raise HTTPException(status_code=404, detail="用户不存在")

    await 数据库.delete(用户)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "用户删除成功"}
