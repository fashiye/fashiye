from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.数据库.会话 import 数据库基类


class 订单状态枚举(enum.Enum):
    待支付 = "pending"
    待审核 = "pending_review"
    已接单 = "accepted"
    进行中 = "in_progress"
    验收中 = "review"
    已完成 = "completed"
    已取消 = "cancelled"
    争议中 = "disputed"
    异常 = "abnormal"


class 订单表(数据库基类):
    """订单主表，存储订单全局信息和状态流转"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    订单号 = Column("order_no", String(32), unique=True, index=True, nullable=False, comment="业务订单号")
    用户ID = Column("user_id", Integer, ForeignKey("users.id"), nullable=False, comment="下单用户 ID")
    游戏ID = Column("game_id", Integer, ForeignKey("games.id"), nullable=False, comment="关联游戏 ID")
    项目ID = Column("project_id", Integer, ForeignKey("projects.id"), nullable=True, comment="关联项目 ID")
    自定义名称 = Column("custom_name", String(100), nullable=True, comment="自定义订单名称")
    自定义描述 = Column("custom_description", Text, nullable=True, comment="自定义订单描述")
    自定义价格 = Column("custom_price", DECIMAL(10, 2), nullable=True, comment="自定义价格")
    数量 = Column("quantity", Integer, nullable=True, comment="购买数量")
    单价 = Column("unit_price", DECIMAL(10, 2), nullable=True, comment="单价")
    总金额 = Column("total_amount", DECIMAL(10, 2), nullable=False, comment="订单总金额")
    状态 = Column("status", String(30), default="pending", index=True, comment="订单状态")
    打手ID = Column("handler_id", Integer, ForeignKey("handlers.id"), nullable=True, comment="接单打手 ID")
    接单时间 = Column("accepted_at", DateTime, nullable=True, comment="打手接单时间")
    账号信息密文 = Column("account_info", Text, nullable=True, comment="游戏账号信息 AES 加密密文")
    需求描述 = Column("requirements", Text, nullable=True, comment="订单需求描述")
    附件 = Column("attachments", Text, nullable=True, comment="附件 JSON 数据")
    完成凭证 = Column("completion_proof", Text, nullable=True, comment="完成凭证 JSON 数据")
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="创建时间")
    更新时间 = Column("updated_at", DateTime, nullable=True, comment="更新时间")
    完成时间 = Column("completed_at", DateTime, nullable=True, comment="订单完成时间")
    取消时间 = Column("cancelled_at", DateTime, nullable=True, comment="订单取消时间")
    用户评分 = Column("user_rating", Integer, nullable=True, comment="用户评星（1-5）")
    用户评论 = Column("user_comment", Text, nullable=True, comment="用户评语")
    打手评分 = Column("handler_rating", Integer, nullable=True, comment="打手评星（1-5）")
    打手评论 = Column("handler_comment", Text, nullable=True, comment="打手评语")
    异常原因 = Column("abnormal_reason", Text, nullable=True, comment="标记异常时的原因说明")

    用户 = relationship("用户表", back_populates="订单列表", foreign_keys=[用户ID])
    打手 = relationship("打手表", back_populates="打手订单列表", foreign_keys=[打手ID])
    游戏 = relationship("游戏表", back_populates="订单列表")
    订单项列表 = relationship("订单项目表", back_populates="订单", cascade="all, delete-orphan")
    操作日志列表 = relationship("订单操作日志表", back_populates="订单", cascade="all, delete-orphan", order_by="订单操作日志表.操作时间.desc()")


class 订单操作日志表(数据库基类):
    """订单操作流水表，记录每次状态变更的审计日志"""

    __tablename__ = "order_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    订单ID = Column("order_id", Integer, ForeignKey("orders.id"), nullable=False, comment="关联订单 ID")
    操作者类型 = Column("operator_type", String(20), nullable=False, comment="操作者类型: user=用户, handler=打手, admin=管理员")
    操作者ID = Column("operator_id", Integer, nullable=False, comment="操作者的用户/打手/管理员 ID")
    动作 = Column("action", String(30), nullable=False, comment="操作动作标识")
    旧状态 = Column("old_status", String(30), nullable=True, comment="操作前的订单状态")
    新状态 = Column("new_status", String(30), nullable=True, comment="操作后的订单状态")
    备注 = Column("remark", String(500), nullable=True, comment="操作备注或原因")
    操作时间 = Column("created_at", DateTime, default=datetime.now, comment="操作时间")

    订单 = relationship("订单表", back_populates="操作日志列表")