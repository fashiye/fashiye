from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum('user_user', 'user_handler', 'handler_admin', 'user_admin'))
    participant_a_type = Column(Enum('user', 'handler', 'admin'))
    participant_a_id = Column(Integer)
    participant_b_type = Column(Enum('user', 'handler', 'admin'))
    participant_b_id = Column(Integer)
    last_message = Column(Text)
    last_message_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_type = Column(Enum('user', 'handler', 'admin'))
    sender_id = Column(Integer)
    content = Column(Text)
    content_type = Column(Enum('text', 'image', 'file', 'order_card'))
    attachment = Column(String(255))
    order_id = Column(Integer, ForeignKey("orders.id"))
    status = Column(Enum('sent', 'delivered', 'read'), default='sent')
    created_at = Column(DateTime, server_default=func.now())
    
    @property
    def senderId(self):
        return self.sender_id
    
    @property
    def senderType(self):
        return self.sender_type
    
    @property
    def contentType(self):
        return self.content_type
    
    @property
    def createdAt(self):
        return self.created_at.isoformat() if self.created_at else None


class MessageReadStatus(Base):
    __tablename__ = "message_read_status"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    participant_type = Column(Enum('user', 'handler', 'admin'))
    participant_id = Column(Integer)
    last_read_message_id = Column(Integer, ForeignKey("messages.id"))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
