from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from app.models.order import Order, OrderLog
from app.models.order_item import OrderItem
from app.models.user import User, Handler
from app.models.game import Project, Game
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderRate
from app.core.exceptions import BusinessError
from app.utils.order_no_generator import generate_order_no
from app.core.crypto import crypto
from typing import Optional, List
from decimal import Decimal


class OrderService:
    @staticmethod
    async def create_order(db: AsyncSession, user: User, order_data: OrderCreate):
        game = await db.get(Game, order_data.gameId)
        if not game or game.status != 1:
            raise BusinessError("游戏不存在或已禁用")

        # 验证所有项目并计算总价
        total_amount = Decimal('0')
        order_items = []
        
        for item_data in order_data.items:
            project = await db.get(Project, item_data.projectId)
            if not project or project.status != 1:
                raise BusinessError(f"项目ID {item_data.projectId} 不存在或已禁用")
            
            unit_price = project.price
            quantity = item_data.quantity
            item_total = unit_price * quantity
            total_amount += item_total
            
            order_items.append({
                'project_id': item_data.projectId,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': item_total,
                'project_name': project.name
            })

        encrypted_account = crypto.encrypt(order_data.accountInfo)

        order = Order(
            order_no=generate_order_no(),
            user_id=user.id,
            game_id=order_data.gameId,
            total_amount=total_amount,
            status='pending_review',
            account_info=encrypted_account,
            requirements=order_data.requirements
        )
        db.add(order)
        await db.flush()

        # 创建订单项目
        for item in order_items:
            order_item = OrderItem(
                order_id=order.id,
                project_id=item['project_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
            db.add(order_item)

        log = OrderLog(
            order_id=order.id,
            operator_type='user',
            operator_id=user.id,
            action='create',
            new_status='pending_review'
        )
        db.add(log)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def get_order(db: AsyncSession, order_id: int):
        """获取订单详情，包含项目明细"""
        result = await db.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.project),
                selectinload(Order.user),
                selectinload(Order.game),
                selectinload(Order.handler)
            )
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        return order

    @staticmethod
    async def get_user_orders(db: AsyncSession, user_id: int, page: int = 1, size: int = 20):
        """获取用户的订单列表，包含项目明细"""
        query = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.project),
                selectinload(Order.user),
                selectinload(Order.game),
                selectinload(Order.handler)
            )
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(query)
        orders = result.scalars().all()
        return orders

    @staticmethod
    async def get_handler_orders(db: AsyncSession, handler_id: int, page: int = 1, size: int = 20):
        """获取打手的订单列表，包含项目明细"""
        query = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.project),
                selectinload(Order.user),
                selectinload(Order.game),
                selectinload(Order.handler)
            )
            .where(Order.handler_id == handler_id)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(query)
        orders = result.scalars().all()
        return orders

    @staticmethod
    async def accept_order(db: AsyncSession, order_id: int, handler: Handler):
        stmt = (
            update(Order)
            .where(Order.id == order_id, Order.status == 'pending')
            .values(status='accepted', handler_id=handler.id, accepted_at=func.now())
        )
        result = await db.execute(stmt)
        
        if result.rowcount == 0:
            raise BusinessError("订单已被抢单或状态已变更", code=409)
        
        updated_order = await db.get(Order, order_id)
        
        log = OrderLog(
            order_id=order_id,
            operator_type='handler',
            operator_id=handler.id,
            action='accept',
            old_status='pending',
            new_status='accepted'
        )
        db.add(log)
        await db.commit()
        await db.refresh(updated_order)
        return updated_order

    @staticmethod
    async def update_order_status(
        db: AsyncSession, 
        order_id: int, 
        action: str, 
        operator_type: str, 
        operator_id: int,
        remark: Optional[str] = None,
        completion_proof: Optional[List[str]] = None
    ):
        order = await db.get(Order, order_id)
        if not order:
            raise BusinessError("订单不存在")

        status_transitions = {
            'start': ('accepted', 'in_progress'),
            'submit_complete': ('in_progress', 'review'),
            'confirm_complete': ('review', 'completed'),
            'cancel': ('pending', 'cancelled'),
            'dispute': ('pending', 'disputed')
        }

        if action not in status_transitions:
            raise BusinessError("无效的操作")

        old_status, new_status = status_transitions[action]
        
        if order.status != old_status:
            raise BusinessError(f"订单状态不允许此操作，当前状态: {order.status}")

        update_data = {'status': new_status}
        
        if action == 'submit_complete' and completion_proof:
            update_data['completion_proof'] = completion_proof
        elif action == 'confirm_complete':
            update_data['completed_at'] = func.now()
        elif action == 'cancel':
            update_data['cancelled_at'] = func.now()

        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(**update_data)
        )

        log = OrderLog(
            order_id=order_id,
            operator_type=operator_type,
            operator_id=operator_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            remark=remark
        )
        db.add(log)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def rate_order(db: AsyncSession, order_id: int, rate_data: OrderRate, user_id: int, role: str):
        order = await db.get(Order, order_id)
        if not order:
            raise BusinessError("订单不存在")
        
        if order.status != 'completed':
            raise BusinessError("只能评价已完成的订单")

        if role == 'user':
            if order.user_rating:
                raise BusinessError("已经评价过了")
            order.user_rating = rate_data.rating
            order.user_comment = rate_data.comment
        else:
            if order.handler_rating:
                raise BusinessError("已经评价过了")
            order.handler_rating = rate_data.rating
            order.handler_comment = rate_data.comment

        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def get_pending_review_orders(db: AsyncSession, page: int = 1, size: int = 20):
        """获取待审核订单列表"""
        query = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.project),
                selectinload(Order.user),
                selectinload(Order.game),
                selectinload(Order.handler)
            )
            .where(Order.status == 'pending_review')
            .order_by(Order.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(query)
        orders = result.scalars().all()
        return orders

    @staticmethod
    async def approve_order(db: AsyncSession, order_id: int, admin_id: int):
        """批准订单"""
        order = await db.get(Order, order_id)
        if not order:
            raise BusinessError("订单不存在")
        
        if order.status != 'pending_review':
            raise BusinessError(f"订单状态不允许此操作，当前状态: {order.status}")
        
        # 更新订单状态
        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status='pending')
        )
        
        # 记录操作日志
        log = OrderLog(
            order_id=order_id,
            operator_type='admin',
            operator_id=admin_id,
            action='approve',
            old_status='pending_review',
            new_status='pending',
            remark='管理员批准订单'
        )
        db.add(log)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def reject_order(db: AsyncSession, order_id: int, admin_id: int, remark: Optional[str] = None):
        """拒绝订单"""
        order = await db.get(Order, order_id)
        if not order:
            raise BusinessError("订单不存在")
        
        if order.status != 'pending_review':
            raise BusinessError(f"订单状态不允许此操作，当前状态: {order.status}")
        
        # 更新订单状态
        await db.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status='cancelled', cancelled_at=func.now())
        )
        
        # 记录操作日志
        log = OrderLog(
            order_id=order_id,
            operator_type='admin',
            operator_id=admin_id,
            action='reject',
            old_status='pending_review',
            new_status='cancelled',
            remark=remark or '管理员拒绝订单'
        )
        db.add(log)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def get_order_pool(db: AsyncSession, game_id: Optional[int] = None, page: int = 1, size: int = 20):
        """获取订单池，包含项目明细"""
        query = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.project))
            .where(Order.status == 'pending')
        )
        
        if game_id:
            query = query.where(Order.game_id == game_id)
        
        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        return orders
