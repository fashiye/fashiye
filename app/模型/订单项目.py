from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.数据库.会话 import 数据库基类


class 订单项目表(数据库基类):
    """订单与项目关联表，记录每个订单包含的项目及数量"""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    订单ID = Column("order_id", Integer, ForeignKey("orders.id"), nullable=False, comment="关联订单 ID")
    项目ID = Column("project_id", Integer, ForeignKey("projects.id"), nullable=False, comment="关联项目 ID")
    项目名称 = Column("project_name", String(200), nullable=True, comment="项目名称快照")
    数量 = Column("quantity", Integer, default=1, comment="购买数量")
    单价 = Column("unit_price", DECIMAL(10, 2), nullable=True, comment="项目单价")
    总价 = Column("total_price", DECIMAL(10, 2), nullable=True, comment="项目小计金额")

    订单 = relationship("订单表", back_populates="订单项列表")
    项目 = relationship("项目表")
