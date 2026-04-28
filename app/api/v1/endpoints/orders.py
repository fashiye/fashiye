from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_role as require_role_dep
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderPoolItem, 
    OrderStatusUpdate, OrderRate, OrderItemResponse
)
from app.services.order_service import OrderService
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.game import Game
from app.models.user import User, Handler
from app.core.exceptions import BusinessError
from app.core.crypto import crypto
from typing import List, Optional

router = APIRouter(prefix="/orders", tags=["orders"])


def build_order_response(order) -> OrderResponse:
    """构建订单响应对象"""
    items = []
    for item in order.items:
        items.append(OrderItemResponse(
            id=item.id,
            projectId=item.project_id,
            projectName=item.project.name if item.project else "",
            quantity=item.quantity,
            unitPrice=item.unit_price,
            totalPrice=item.total_price
        ))
    
    if not items and order.project_id:
        items.append(OrderItemResponse(
            id=0,
            projectId=order.project_id,
            projectName=order.project.name if order.project else (order.custom_name or ""),
            quantity=order.quantity or 1,
            unitPrice=order.unit_price or order.total_amount,
            totalPrice=order.total_amount
        ))
    
    account_info_decrypted = None
    if order.account_info:
        try:
            account_info_decrypted = crypto.decrypt(order.account_info)
        except Exception:
            account_info_decrypted = "[加密数据]"
    
    return OrderResponse(
        id=order.id,
        orderNo=order.order_no,
        userId=order.user_id,
        userName=order.user.username if order.user else None,
        gameId=order.game_id,
        gameName=order.game.name if order.game else None,
        items=items,
        totalAmount=order.total_amount,
        status=order.status,
        handlerId=order.handler_id,
        handlerName=order.handler.username if order.handler else None,
        acceptedAt=order.accepted_at,
        accountInfo=account_info_decrypted,
        requirements=order.requirements,
        attachments=order.attachments,
        completionProof=order.completion_proof,
        createdAt=order.created_at,
        updatedAt=order.updated_at,
        completedAt=order.completed_at,
        cancelledAt=order.cancelled_at,
        userRating=order.user_rating,
        userComment=order.user_comment,
        handlerRating=order.handler_rating,
        handlerComment=order.handler_comment
    )


def build_item_summary(order) -> str:
    """构建项目摘要，如：排位赛代打 x5, 日常任务 x10"""
    if order.items:
        summaries = []
        for item in order.items:
            project_name = item.project.name if item.project else "未知项目"
            summaries.append(f"{project_name} x{item.quantity}")
        return ", ".join(summaries[:3])
    
    if order.project_id and order.project:
        return f"{order.project.name} x{order.quantity or 1}"
    elif order.custom_name:
        return f"自定义：{order.custom_name}"
    
    return "未知项目"


@router.post("", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["user"]))
):
    user, _ = user_role
    order = await OrderService.create_order(db, user, order_data)
    order = await OrderService.get_order(db, order.id)
    return build_order_response(order)


@router.get("/pool", response_model=List[OrderPoolItem])
async def get_order_pool(
    game_id: int = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["handler", "super", "operator"]))
):
    orders = await OrderService.get_order_pool(db, game_id, page, size)
    
    result = []
    for order in orders:
        game_name = order.game.name if order.game else ""
        item_summary = build_item_summary(order)
        
        result.append(OrderPoolItem(
            id=order.id,
            orderNo=order.order_no,
            gameName=game_name,
            itemSummary=item_summary,
            totalAmount=order.total_amount,
            requirements=order.requirements,
            createdAt=order.created_at
        ))
    
    return result


@router.get("/all", response_model=List[OrderResponse])
async def get_all_orders(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super", "operator"]))
):
    admin, _ = user_role
    
    query = select(Order).options(
        selectinload(Order.user),
        selectinload(Order.handler),
        selectinload(Order.game),
        selectinload(Order.items).selectinload(OrderItem.project)
    )
    
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [build_order_response(order) for order in orders]


@router.get("/my", response_model=List[OrderResponse])
async def get_my_orders(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    if role == "user":
        orders = await OrderService.get_user_orders(db, user.id, page, size)
    elif role == "handler":
        orders = await OrderService.get_handler_orders(db, user.id, page, size)
    else:
        orders = []
    
    return [build_order_response(order) for order in orders]


@router.get("/pending-review", response_model=List[OrderResponse])
async def get_pending_review_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super", "operator"]))
):
    admin, _ = user_role
    orders = await OrderService.get_pending_review_orders(db, page, size)
    return [build_order_response(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise BusinessError("订单不存在", code=404)
    
    if role == "user" and order.user_id != user.id:
        raise BusinessError("无权访问此订单", code=403)
    if role == "handler" and order.handler_id != user.id:
        raise BusinessError("无权访问此订单", code=403)
    
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.user),
            selectinload(Order.handler),
            selectinload(Order.game)
        )
        .where(Order.id == order_id)
    )
    order_with_relations = result.scalar_one()
    
    return build_order_response(order_with_relations)


@router.post("/{order_id}/accept", response_model=OrderResponse)
async def accept_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["handler"]))
):
    handler, _ = user_role
    order = await OrderService.accept_order(db, order_id, handler)
    order = await OrderService.get_order(db, order.id)
    return build_order_response(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    order = await OrderService.update_order_status(
        db, order_id, "cancel", role, user.id
    )
    order = await OrderService.get_order(db, order.id)
    return build_order_response(order)


@router.post("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise BusinessError("订单不存在", code=404)
    
    if role == "user" and order.user_id != user.id:
        raise BusinessError("无权操作此订单", code=403)
    if role == "handler" and order.handler_id != user.id:
        raise BusinessError("无权操作此订单", code=403)
    
    order = await OrderService.update_order_status(
        db, order_id, status_data.action, role, user.id,
        status_data.remark, status_data.completionProof
    )
    
    order = await OrderService.get_order(db, order.id)
    return build_order_response(order)


@router.post("/{order_id}/approve", response_model=OrderResponse)
async def approve_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super", "operator"]))
):
    admin, _ = user_role
    order = await OrderService.approve_order(db, order_id, admin.id)
    order = await OrderService.get_order(db, order.id)
    return build_order_response(order)


@router.post("/{order_id}/reject", response_model=OrderResponse)
async def reject_order(
    order_id: int,
    remark: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super", "operator"]))
):
    admin, _ = user_role
    order = await OrderService.reject_order(db, order_id, admin.id, remark)
    order = await OrderService.get_order(db, order.id)
    return build_order_response(order)


@router.post("/{order_id}/rate")
async def rate_order(
    order_id: int,
    rate_data: OrderRate,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    if role != rate_data.role:
        raise BusinessError("角色不匹配")
    
    await OrderService.rate_order(db, order_id, rate_data, user.id, role)
    
    return {"code": 0, "data": None, "message": "评价成功"}


@router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role_dep(["super", "operator"]))
):
    admin, _ = user_role
    
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise BusinessError("订单不存在", code=404)
    
    if order.status == "in_progress":
        raise BusinessError("无法删除进行中的订单", code=400)
    
    await db.delete(order)
    await db.commit()
    
    return {"code": 0, "data": None, "message": "订单删除成功"}