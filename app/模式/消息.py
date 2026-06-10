from pydantic import BaseModel
from typing import Optional


class 消息创建(BaseModel):
    """发送消息的请求体"""
    content: str
    contentType: str = "text"
    attachment: Optional[str] = None
    orderId: Optional[int] = None


class 消息响应(BaseModel):
    """消息的响应数据结构"""
    id: int
    senderId: int
    senderType: str
    content: str
    contentType: str
    attachment: Optional[str] = None
    orderId: Optional[int] = None
    status: Optional[str] = None
    createdAt: str

    class Config:
        from_attributes = True


class 会话创建请求(BaseModel):
    """创建会话的请求体"""
    otherPartyType: str
    otherPartyId: int
    type: str = "user_handler"
    orderId: Optional[int] = None


class 会话响应(BaseModel):
    """会话列表项的响应数据结构"""
    id: int
    type: str
    otherPartyId: int
    otherPartyUsername: str
    otherPartyAvatar: Optional[str] = None
    otherPartyRole: str
    lastMessage: Optional[str] = None
    lastMessageAt: Optional[str] = None
    unreadCount: int = 0


class 标记已读请求(BaseModel):
    """标记消息为已读的请求体"""
    last_read_message_id: int
