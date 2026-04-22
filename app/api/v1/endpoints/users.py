from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_role as require_role_dep
from app.models.user import User, Handler, Admin
from app.models.order import Order
from sqlalchemy.orm import selectinload
from typing import List

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[dict])
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
        query = query.offset((page - 1) * size).limit(size)
        
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
        query = query.offset((page - 1) * size).limit(size)
        
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
        query = query.offset((page - 1) * size).limit(size)
        
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
    
    return user_list[:size]


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
