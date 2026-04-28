from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_role as require_role_dep
from app.models.user import User, Handler, Admin
from app.models.order import Order
from sqlalchemy.orm import selectinload
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


class PaginatedUsersResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int


@router.get("", response_model=PaginatedUsersResponse)
async def get_all_users(
    status: str = Query(None),
    role: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super", "operator"]))
):
    admin, _ = user_role
    
    user_list = []
    
    if not role or role == "user":
        query = select(User)
        if status:
            query = query.where(User.status == (1 if status == "active" else 0))
        query = query.order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()
        
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": "user",
                "status": user.status,
                "createdAt": user.created_at.isoformat() if user.created_at else None
            })
    
    if not role or role == "handler":
        query = select(Handler)
        if status:
            query = query.where(Handler.status == (1 if status == "active" else 0))
        query = query.order_by(Handler.created_at.desc())
        result = await db.execute(query)
        handlers = result.scalars().all()
        
        for handler in handlers:
            user_list.append({
                "id": handler.id,
                "username": handler.username,
                "email": handler.email,
                "role": "handler",
                "status": handler.status,
                "createdAt": handler.created_at.isoformat() if handler.created_at else None
            })
    
    if not role or role == "admin":
        query = select(Admin)
        if status:
            query = query.where(Admin.status == (1 if status == "active" else 0))
        query = query.order_by(Admin.created_at.desc())
        result = await db.execute(query)
        admins = result.scalars().all()
        
        for admin in admins:
            user_list.append({
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "role": "admin",
                "status": admin.status,
                "createdAt": admin.created_at.isoformat() if admin.created_at else None
            })
    
    user_list.sort(key=lambda x: x["createdAt"] or "", reverse=True)
    
    total_count = len(user_list)
    
    import math
    pages = math.ceil(total_count / size) if total_count > 0 else 1
    
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_list = user_list[start_idx:end_idx]
    
    return PaginatedUsersResponse(
        items=paginated_list,
        total=total_count,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/available", response_model=List[dict])
async def get_available_users(
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    user_list = []

    if role == "user":
        query = (
            select(Order)
            .options(selectinload(Order.handler), selectinload(Order.game), selectinload(Order.project))
            .where(Order.user_id == user.id, Order.handler_id.isnot(None))
            .order_by(Order.created_at.desc())
        )
        result = await db.execute(query)
        orders = result.scalars().all()
        seen = set()
        for order in orders:
            if order.handler_id and order.handler_id not in seen:
                seen.add(order.handler_id)
                project_name = order.project.name if order.project else (order.custom_name or "")
                user_list.append({
                    "id": order.handler.id,
                    "username": order.handler.username,
                    "role": "handler",
                    "orderNo": order.order_no,
                    "orderInfo": f"{order.game.name} - {project_name}"
                })
    elif role == "handler":
        query = (
            select(Order)
            .options(selectinload(Order.user), selectinload(Order.game), selectinload(Order.project))
            .where(Order.handler_id == user.id)
            .order_by(Order.created_at.desc())
        )
        result = await db.execute(query)
        orders = result.scalars().all()
        seen = set()
        for order in orders:
            if order.user_id and order.user_id not in seen:
                seen.add(order.user_id)
                project_name = order.project.name if order.project else (order.custom_name or "")
                user_list.append({
                    "id": order.user.id,
                    "username": order.user.username,
                    "role": "user",
                    "orderNo": order.order_no,
                    "orderInfo": f"{order.game.name} - {project_name}"
                })
    elif role == "admin":
        query = (
            select(Order)
            .options(selectinload(Order.user), selectinload(Order.handler), selectinload(Order.game), selectinload(Order.project))
            .order_by(Order.created_at.desc())
        )
        result = await db.execute(query)
        orders = result.scalars().all()
        seen = set()
        for order in orders:
            if order.user_id and order.user_id not in seen:
                seen.add(order.user_id)
                user_list.append({
                    "id": order.user.id,
                    "username": order.user.username,
                    "role": "user",
                    "orderNo": order.order_no,
                    "orderInfo": f"{order.game.name}"
                })
            if order.handler_id and order.handler_id not in seen:
                seen.add(order.handler_id)
                user_list.append({
                    "id": order.handler.id,
                    "username": order.handler.username,
                    "role": "handler",
                    "orderNo": order.order_no,
                    "orderInfo": f"{order.game.name}"
                })

    return user_list


@router.delete("/{user_id}")
async def 删除用户(
    user_id: int,
    role: str = Query(..., description="用户角色: user, handler, admin"),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super"]))
):
    """
    删除用户（仅超级管理员可用）
    
    参数:
        user_id: 用户ID
        role: 用户角色（user/handler/admin）
        
    返回:
        删除结果
    """
    admin, _ = user_role
    
    # 根据角色获取对应的模型
    模型映射 = {
        "user": User,
        "handler": Handler,
        "admin": Admin
    }
    
    if role not in 模型映射:
        raise HTTPException(status_code=400, detail="无效的用户角色")
    
    模型类 = 模型映射[role]
    
    # 查询用户
    查询结果 = await db.execute(select(模型类).where(模型类.id == user_id))
    用户 = 查询结果.scalar_one_or_none()
    
    if not 用户:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 防止删除自己
    if role == "admin" and 用户.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    # 检查是否有关联的订单
    if role == "user":
        订单查询 = select(Order).where(Order.user_id == user_id)
        订单结果 = await db.execute(订单查询)
        订单列表 = 订单结果.scalars().all()
        if 订单列表:
            raise HTTPException(
                status_code=400, 
                detail=f"该用户有 {len(订单列表)} 个关联订单，无法删除"
            )
    elif role == "handler":
        订单查询 = select(Order).where(Order.handler_id == user_id)
        订单结果 = await db.execute(订单查询)
        订单列表 = 订单结果.scalars().all()
        if 订单列表:
            raise HTTPException(
                status_code=400, 
                detail=f"该接单员有 {len(订单列表)} 个关联订单，无法删除"
            )
    
    # 删除用户
    await db.delete(用户)
    await db.commit()
    
    return {
        "success": True,
        "message": f"成功删除{role}用户: {用户.username}",
        "deleted_user": {
            "id": 用户.id,
            "username": 用户.username,
            "email": 用户.email,
            "role": role
        }
    }
