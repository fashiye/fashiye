from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import 数据库基类


class 会话表(数据库基类):
    """用户-打手会话表，记录双方聊天关系"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    参与方A类型 = Column(String(20), nullable=False, comment="参与方A角色类型: user/handler")
    参与方AID = Column(Integer, nullable=False, comment="参与方A的用户/打手 ID")
    参与方B类型 = Column(String(20), nullable=False, comment="参与方B角色类型: user/handler")
    参与方BID = Column(Integer, nullable=False, comment="参与方B的用户/打手 ID")
    订单ID = Column(Integer, ForeignKey("orders.id"), nullable=True, comment="关联的订单 ID（可选）")
    类型 = Column(String(20), default="chat", comment="会话类型: chat=聊天, order=订单相关")
    最后消息 = Column[str](Text, nullable=True, comment="最后一条消息的内容摘要")
    最后消息时间 = Column(DateTime, nullable=True, comment="最后一条消息的时间")
    创建时间 = Column(DateTime, default=datetime.now, comment="会话创建时间")
    最后活跃时间 = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="最后活跃时间")


class 消息表(数据库基类):
    """消息记录表，存储会话中的每一条消息"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    会话ID = Column(Integer, ForeignKey("conversations.id"), nullable=False, comment="所属会话 ID")
    发送者ID = Column(Integer, nullable=False, comment="发送者的用户/打手 ID")
    发送者类型 = Column(String(20), nullable=False, comment="发送者类型: user=用户, handler=打手")
    消息类型 = Column(String(20), default="text", comment="消息类型: text=文本, image=图片, system=系统消息")
    内容 = Column(Text, nullable=False, comment="消息正文内容")
    附件 = Column(Text, nullable=True, comment="附件 JSON 数据")
    订单ID = Column(Integer, nullable=True, comment="关联的订单 ID")
    状态 = Column(String(20), default="sent", comment="消息状态: sent=已发送, read=已读")
    发送时间 = Column(DateTime, default=datetime.now, comment="消息发送时间")


class 消息阅读状态表(数据库基类):
    """消息已读状态表，记录每个用户在会话中的最后阅读位置"""

    __tablename__ = "message_read_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    会话ID = Column(Integer, ForeignKey("conversations.id"), nullable=False, comment="会话 ID")
    参与方类型 = Column(String(20), nullable=False, comment="参与方角色类型: user/handler")
    参与方ID = Column(Integer, nullable=False, comment="参与方的用户/打手 ID")
    最后阅读消息ID = Column(Integer, ForeignKey("messages.id"), nullable=False, comment="最后一条已读消息的 ID")
    阅读时间 = Column(DateTime, default=datetime.now, comment="阅读时间")
