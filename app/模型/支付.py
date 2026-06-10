from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Text
from datetime import datetime
from app.数据库.会话 import 数据库基类


class 支付记录表(数据库基类):
    """支付记录表，记录每笔支付订单在 iDataRiver 平台的映射关系和状态"""

    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 内部订单ID，对应 orders 表
    内部订单ID = Column("internal_order_id", Integer, nullable=False, comment="内部订单 ID")
    # iDataRiver 平台返回的订单 ID
    支付平台订单ID = Column("payment_order_id", String(64), unique=True, nullable=True, comment="iDataRiver 订单 ID")
    # 支付金额（元）
    支付金额 = Column("amount", DECIMAL(10, 2), nullable=False, comment="支付金额（元）")
    # 支付状态: pending=待支付, paid=已支付, expired=已过期, refunded=已退款
    支付状态 = Column("payment_status", String(20), default="pending", comment="支付状态")
    # iDataRiver 返回的支付方式 method
    支付方式 = Column("pay_method", String(32), nullable=True, comment="支付方式 method")
    # 支付平台返回的支付链接
    支付链接 = Column("pay_url", Text, nullable=True, comment="支付跳转链接")
    # 创建时间
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="创建时间")
    # 支付完成时间
    支付时间 = Column("paid_at", DateTime, nullable=True, comment="支付完成时间")
    # 回调通知原始数据（JSON 字符串）
    回调原始数据 = Column("callback_raw", Text, nullable=True, comment="回调通知原始数据")
