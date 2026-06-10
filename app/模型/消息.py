from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.数据库.会话 import 数据库基类


class 会话表(数据库基类):
    """用户-打手会话表，记录双方聊天关系"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    类型 = Column("type", String(30), nullable=True, comment="会话类型: user_user/user_handler/handler_admin/user_admin")
    参与方A类型 = Column("participant_a_type", String(20), nullable=True, comment="参与方A角色类型: user/handler/admin")
    参与方AID = Column("participant_a_id", Integer, nullable=True, comment="参与方A的用户/打手/管理员 ID")
    参与方B类型 = Column("participant_b_type", String(20), nullable=True, comment="参与方B角色类型: user/handler/admin")
    参与方BID = Column("participant_b_id", Integer, nullable=True, comment="参与方B的用户/打手/管理员 ID")
    最后消息 = Column("last_message", Text, nullable=True, comment="最后一条消息的内容摘要")
    最后消息时间 = Column("last_message_at", DateTime, nullable=True, comment="最后一条消息的时间")
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="会话创建时间")
    更新时间 = Column("updated_at", DateTime, nullable=True, comment="更新时间")


class 消息表(数据库基类):
    """消息记录表，存储会话中的每一条消息"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    会话ID = Column("conversation_id", Integer, ForeignKey("conversations.id"), nullable=False, comment="所属会话 ID")
    发送者类型 = Column("sender_type", String(20), nullable=True, comment="发送者类型: user/handler/admin")
    发送者ID = Column("sender_id", Integer, nullable=True, comment="发送者的用户/打手/管理员 ID")
    内容 = Column("content", Text, nullable=True, comment="消息正文内容")
    内容类型 = Column("content_type", String(20), nullable=True, comment="消息类型: text/image/file/order_card")
    附件 = Column("attachment", String(255), nullable=True, comment="附件路径")
    订单ID = Column("order_id", Integer, nullable=True, comment="关联的订单 ID")
    状态 = Column("status", String(20), nullable=True, comment="消息状态: sent/delivered/read")
    发送时间 = Column("created_at", DateTime, default=datetime.now, comment="消息发送时间")


class 消息阅读状态表(数据库基类):
    """消息已读状态表，记录每个用户在会话中的最后阅读位置"""

    __tablename__ = "message_read_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    会话ID = Column("conversation_id", Integer, ForeignKey("conversations.id"), nullable=False, comment="会话 ID")
    参与方类型 = Column("participant_type", String(20), nullable=False, comment="参与方角色类型: user/handler/admin")
    参与方ID = Column("participant_id", Integer, nullable=False, comment="参与方的用户/打手/管理员 ID")
    最后阅读消息ID = Column("last_read_message_id", Integer, ForeignKey("messages.id"), nullable=False, comment="最后一条已读消息的 ID")
    阅读时间 = Column("updated_at", DateTime, default=datetime.now, comment="阅读时间")