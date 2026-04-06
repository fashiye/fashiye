from pydantic import BaseModel
from typing import Optional, List


class MessageCreate(BaseModel):
    content: str
    contentType: str = "text"
    attachment: Optional[str] = None
    orderId: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    senderId: int
    senderType: str
    content: str
    contentType: str
    attachment: Optional[str] = None
    orderId: Optional[int] = None
    status: str
    createdAt: str
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    type: str
    otherPartyId: int
    otherPartyUsername: str
    otherPartyAvatar: Optional[str] = None
    otherPartyRole: str
    lastMessage: Optional[str] = None
    lastMessageAt: Optional[str] = None
    unreadCount: int = 0


class MarkReadRequest(BaseModel):
    last_read_message_id: int
