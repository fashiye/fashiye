from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_role
from app.schemas.message import MessageCreate, MessageResponse, ConversationResponse, MarkReadRequest
from app.services.message_service import MessageService
from app.models.message import Conversation, Message
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    otherPartyType: str
    otherPartyId: int
    type: str = "user_handler"


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    conv_data: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    # 检查会话是否已存在
    existing_conv = await db.execute(
        select(Conversation).where(
            ((Conversation.participant_a_type == role) & (Conversation.participant_a_id == user.id) &
             (Conversation.participant_b_type == conv_data.otherPartyType) & (Conversation.participant_b_id == conv_data.otherPartyId)) |
            ((Conversation.participant_a_type == conv_data.otherPartyType) & (Conversation.participant_a_id == conv_data.otherPartyId) &
             (Conversation.participant_b_type == role) & (Conversation.participant_b_id == user.id))
        )
    )
    existing_conv = existing_conv.scalar_one_or_none()
    
    if existing_conv:
        raise HTTPException(status_code=400, detail="会话已存在")
    
    # 获取对方用户信息
    other_party = None
    if conv_data.otherPartyType == "user":
        from app.models.user import User
        other_party = await db.get(User, conv_data.otherPartyId)
    elif conv_data.otherPartyType == "handler":
        from app.models.user import Handler
        other_party = await db.get(Handler, conv_data.otherPartyId)
    elif conv_data.otherPartyType == "admin":
        from app.models.user import Admin
        other_party = await db.get(Admin, conv_data.otherPartyId)
    
    if not other_party:
        raise HTTPException(status_code=404, detail="对方用户不存在")
    
    # 创建新会话
    conversation = Conversation(
        type=conv_data.type,
        participant_a_type=role,
        participant_a_id=user.id,
        participant_b_type=conv_data.otherPartyType,
        participant_b_id=conv_data.otherPartyId
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse(
        id=conversation.id,
        type=conversation.type,
        otherPartyId=conv_data.otherPartyId,
        otherPartyUsername=other_party.username if other_party else "",
        otherPartyAvatar=other_party.avatar if other_party else None,
        otherPartyRole=conv_data.otherPartyType,
        lastMessage=None,
        lastMessageAt=None,
        unreadCount=0
    )


@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    conversations = await MessageService.get_conversations(db, role, user.id, page, size)
    
    result = []
    for conv in conversations:
        other_party_id = None
        other_party_type = None
        
        if conv.participant_a_type == role and conv.participant_a_id == user.id:
            other_party_id = conv.participant_b_id
            other_party_type = conv.participant_b_type
        else:
            other_party_id = conv.participant_a_id
            other_party_type = conv.participant_a_type
        
        other_party = None
        if other_party_type == "user":
            from app.models.user import User
            other_party = await db.get(User, other_party_id)
        elif other_party_type == "handler":
            from app.models.user import Handler
            other_party = await db.get(Handler, other_party_id)
        elif other_party_type == "admin":
            from app.models.user import Admin
            other_party = await db.get(Admin, other_party_id)
        
        unread_count = await MessageService.get_unread_count(db, conv.id, role, user.id)
        
        result.append(ConversationResponse(
            id=conv.id,
            type=conv.type,
            otherPartyId=other_party_id,
            otherPartyUsername=other_party.username if other_party else "",
            otherPartyAvatar=other_party.avatar if other_party else None,
            otherPartyRole=other_party_type,
            lastMessage=conv.last_message,
            lastMessageAt=conv.last_message_at.isoformat() if conv.last_message_at else None,
            unreadCount=unread_count
        ))
    
    return result


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    before: int = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    is_participant = (
        (conv.participant_a_type == role and conv.participant_a_id == user.id) or
        (conv.participant_b_type == role and conv.participant_b_id == user.id)
    )
    
    if not is_participant:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    messages = await MessageService.get_messages(db, conversation_id, before, limit)
    
    return messages


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    is_participant = (
        (conv.participant_a_type == role and conv.participant_a_id == user.id) or
        (conv.participant_b_type == role and conv.participant_b_id == user.id)
    )
    
    if not is_participant:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    message = await MessageService.send_message(
        db, conversation_id, role, user.id, message_data
    )
    
    return message


@router.post("/{conversation_id}/read")
async def mark_read(
    conversation_id: int,
    read_data: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, role = user_role
    
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    is_participant = (
        (conv.participant_a_type == role and conv.participant_a_id == user.id) or
        (conv.participant_b_type == role and conv.participant_b_id == user.id)
    )
    
    if not is_participant:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    await MessageService.mark_read(
        db, conversation_id, role, user.id, read_data.last_read_message_id
    )
    
    return {"code": 0, "data": None, "message": "已更新已读位置"}
