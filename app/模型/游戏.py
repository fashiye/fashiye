from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.数据库.会话 import 数据库基类


class 游戏表(数据库基类):
    """游戏分类表，定义可接单的游戏类型"""

    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    名称 = Column("name", String(100), nullable=True, comment="游戏名称")
    图标 = Column("icon", String(255), nullable=True, comment="游戏图标 URL")
    状态 = Column("status", Integer, nullable=True, comment="状态: 0=停用, 1=启用")
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="创建时间")
    更新时间 = Column("updated_at", DateTime, nullable=True, comment="更新时间")
    描述 = Column("description", Text, nullable=True, comment="游戏简介")

    项目列表 = relationship("项目表", back_populates="游戏", cascade="all, delete-orphan")
    订单列表 = relationship("订单表", back_populates="游戏")


class 项目表(数据库基类):
    """游戏项目/服务表，定义每个游戏下可购买的服务项"""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    游戏ID = Column("game_id", Integer, ForeignKey("games.id"), nullable=False, comment="关联游戏 ID")
    名称 = Column("name", String(100), nullable=True, comment="项目名称")
    描述 = Column("description", Text, nullable=True, comment="项目详细说明")
    价格类型 = Column("price_type", String(20), nullable=True, comment="计价方式: fixed=一口价, unit=按量计价")
    价格 = Column("price", Integer, nullable=True, comment="价格，单位：分")
    单位名称 = Column("unit_name", String(20), nullable=True, comment="单位名称")
    最大数量 = Column("max_quantity", Integer, nullable=True, comment="最大购买数量")
    排序 = Column("sort", Integer, nullable=True, comment="排序字段")
    状态 = Column("status", Integer, nullable=True, comment="状态: 0=停用, 1=启用")
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="创建时间")
    更新时间 = Column("updated_at", DateTime, nullable=True, comment="更新时间")
    图标 = Column("icon", String(255), nullable=True, comment="项目图标 URL")
    每单限购 = Column("is_single_per_order", Integer, default=0, comment="是否每单限购")

    游戏 = relationship("游戏表", back_populates="项目列表")