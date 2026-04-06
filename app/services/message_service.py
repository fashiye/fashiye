from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, case
from app.models.message import Conversation, Message, MessageReadStatus
from app.schemas.message import MessageCreate, MarkReadRequest
from typing import Optional, List


class MessageService:
    @staticmethod
    async def get_conversations(db: AsyncSession, user_type: str, user_id: int, page: int = 1, size: int = 20):
        query = select(Conversation).where(
            (Conversation.participant_a_type == user_type) & (Conversation.participant_a_id == user_id) |
            (Conversation.participant_b_type == user_type) & (Conversation.participant_b_id == user_id)
        )
        query = query.order_by(
            case(
                (Conversation.last_message_at == None, 1),
                else_=0
            ).asc(),
            Conversation.last_message_at.desc()
        )
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        return conversations

    @staticmethod
    async def get_messages(
        db: AsyncSession, 
        conversation_id: int, 
        before: Optional[int] = None, 
        limit: int = 20
    ):
        query = select(Message).where(Message.conversation_id == conversation_id)
        
        if before:
            query = query.where(Message.id < before)
        
        query = query.order_by(Message.created_at.desc())
        query = query.limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return list(reversed(messages))

    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: int,
        sender_type: str,
        sender_id: int,
        message_data: MessageCreate
    ):
        message = Message(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=message_data.content,
            content_type=message_data.contentType,
            attachment=message_data.attachment,
            order_id=message_data.orderId
        )
        db.add(message)
        
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                last_message=message_data.content,
                last_message_at=func.now()
            )
        )
        
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def mark_read(
        db: AsyncSession,
        conversation_id: int,
        participant_type: str,
        participant_id: int,
        last_read_message_id: int
    ):
        read_status = await db.execute(
            select(MessageReadStatus).where(
                MessageReadStatus.conversation_id == conversation_id,
                MessageReadStatus.participant_type == participant_type,
                MessageReadStatus.participant_id == participant_id
            )
        )
        read_status = read_status.scalar_one_or_none()
        
        if read_status:
            read_status.last_read_message_id = last_read_message_id
        else:
            read_status = MessageReadStatus(
                conversation_id=conversation_id,
                participant_type=participant_type,
                participant_id=participant_id,
                last_read_message_id=last_read_message_id
            )
            db.add(read_status)
        
        await db.commit()
        return read_status

    @staticmethod
    async def get_unread_count(
        db: AsyncSession,
        conversation_id: int,
        participant_type: str,
        participant_id: int
    ):
        read_status = await db.execute(
            select(MessageReadStatus).where(
                MessageReadStatus.conversation_id == conversation_id,
                MessageReadStatus.participant_type == participant_type,
                MessageReadStatus.participant_id == participant_id
            )
        )
        read_status = read_status.scalar_one_or_none()
        
        if not read_status or not read_status.last_read_message_id:
            query = select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
            result = await db.execute(query)
            return result.scalar()
        
        query = select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.id > read_status.last_read_message_id
        )
        result = await db.execute(query)
        return result.scalar()
