from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    # 保留原有字段用于兼容历史订单
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    custom_name = Column(String(100))
    custom_description = Column(Text)
    custom_price = Column(DECIMAL(10, 2))
    quantity = Column(Integer, default=1)
    unit_price = Column(DECIMAL(10, 2), nullable=True)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum('pending', 'pending_review', 'accepted', 'in_progress', 'review', 'completed', 'cancelled', 'disputed'),
                    default='pending_review', nullable=False)
    handler_id = Column(Integer, ForeignKey("handlers.id"), nullable=True)
    accepted_at = Column(DateTime)
    account_info = Column(Text)
    requirements = Column(Text)
    attachments = Column(JSON)
    completion_proof = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    user_rating = Column(Integer)
    user_comment = Column(Text)
    handler_rating = Column(Integer)
    handler_comment = Column(Text)
    
    user = relationship("User")
    handler = relationship("Handler")
    game = relationship("Game")
    project = relationship("Project")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderLog(Base):
    __tablename__ = "order_logs"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    operator_type = Column(Enum('user', 'handler', 'admin'), nullable=False)
    operator_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    old_status = Column(String(20))
    new_status = Column(String(20), nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
