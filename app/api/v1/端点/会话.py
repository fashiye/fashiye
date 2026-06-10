from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.数据库.会话 import 获取数据库会话
from app.api.依赖.认证 import 获取当前用户
from app.服务.消息服务 import 消息服务
from app.模式.消息 import 消息创建, 消息响应, 会话响应, 会话创建请求, 标记已读请求
from app.模型.消息 import 会话表, 消息表, 消息阅读状态表
from app.模型.用户 import 用户表, 打手表
from app.核心.异常 import 业务逻辑错误

router = APIRouter()


@router.get("/conversations")
async def 获取会话列表接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取当前用户的所有会话列表"""
    当前用户, 当前角色 = 当前用户信息
    会话列表 = await 消息服务.获取会话列表(数据库, 当前角色, 当前用户.id)

    结果列表 = []
    for 会话 in 会话列表:
        if 会话.参与方A类型 == 当前角色 and 会话.参与方AID == 当前用户.id:
            对方类型 = 会话.参与方B类型
            对方ID = 会话.参与方BID
        else:
            对方类型 = 会话.参与方A类型
            对方ID = 会话.参与方AID

        对方用户名 = "未知"
        if 对方类型 == "user":
            用户结果 = await 数据库.execute(select(用户表).where(用户表.id == 对方ID))
            用户 = 用户结果.scalar_one_or_none()
            if 用户:
                对方用户名 = 用户.用户名
        elif 对方类型 == "handler":
            打手结果 = await 数据库.execute(select(打手表).where(打手表.id == 对方ID))
            打手 = 打手结果.scalar_one_or_none()
            if 打手:
                对方用户名 = 打手.用户名

        未读数量 = await 消息服务.获取未读数量(数据库, 会话.id, 当前角色, 当前用户.id)

        结果列表.append(会话响应(
            id=会话.id,
            type=会话.类型,
            otherPartyId=对方ID,
            otherPartyUsername=对方用户名,
            otherPartyRole=对方类型,
            lastMessage=会话.最后消息,
            lastMessageAt=会话.最后消息时间.isoformat() if 会话.最后消息时间 else None,
            unreadCount=未读数量
        ))

    return {"code": 0, "data": 结果列表, "message": "获取会话列表成功"}


@router.post("/conversations")
async def 创建会话接口(
    创建数据: 会话创建请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """
    创建新会话或返回已有会话
    传入：otherPartyType(对方角色), otherPartyId(对方ID), type(会话类型), orderId(可选订单ID)
    作用：调用消息服务创建或查找已有会话
    传出：包含会话ID的响应
    """
    当前用户, 当前角色 = 当前用户信息

    会话 = await 消息服务.创建会话(
        数据库,
        发起方类型=当前角色,
        发起方ID=当前用户.id,
        对方类型=创建数据.otherPartyType,
        对方ID=创建数据.otherPartyId,
        会话类型=创建数据.type,
        订单ID=创建数据.orderId,
    )
    return {"code": 0, "data": {"id": 会话.id}, "message": "创建会话成功"}


@router.get("/conversations/{conversation_id}/messages")
async def 获取消息列表接口(
    conversation_id: int,
    起始消息ID: Optional[int] = Query(None, description="起始消息ID，用于分页加载更早的消息"),
    限制数量: int = Query(20, ge=1, le=100, description="返回消息数量"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取指定会话的消息记录，支持分页"""
    当前用户, 当前角色 = 当前用户信息

    会话结果 = await 数据库.execute(select(会话表).where(会话表.id == conversation_id))
    会话 = 会话结果.scalar_one_or_none()
    if not 会话:
        raise 业务逻辑错误("会话不存在")
    if not (会话.参与方A类型 == 当前角色 and 会话.参与方AID == 当前用户.id) and \
       not (会话.参与方B类型 == 当前角色 and 会话.参与方BID == 当前用户.id):
        raise 业务逻辑错误("无权访问此会话")

    消息列表 = await 消息服务.获取消息列表(数据库, conversation_id, 起始消息ID, 限制数量)

    消息响应列表 = [消息响应(
        id=msg.id,
        senderId=msg.发送者ID,
        senderType=msg.发送者类型,
        content=msg.内容,
        contentType=msg.内容类型,
        attachment=msg.附件,
        orderId=msg.订单ID,
        status=msg.状态,
        createdAt=msg.发送时间.isoformat() if msg.发送时间 else ""
    ) for msg in 消息列表]

    return {"code": 0, "data": 消息响应列表, "message": "获取消息成功"}


@router.post("/conversations/{conversation_id}/messages")
async def 发送消息接口(
    conversation_id: int,
    消息数据: 消息创建,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """在指定会话中发送消息"""
    当前用户, 当前角色 = 当前用户信息

    会话结果 = await 数据库.execute(select(会话表).where(会话表.id == conversation_id))
    会话 = 会话结果.scalar_one_or_none()
    if not 会话:
        raise 业务逻辑错误("会话不存在")
    if not (会话.参与方A类型 == 当前角色 and 会话.参与方AID == 当前用户.id) and \
       not (会话.参与方B类型 == 当前角色 and 会话.参与方BID == 当前用户.id):
        raise 业务逻辑错误("无权访问此会话")

    消息 = await 消息服务.发送消息(
        数据库, conversation_id, 当前角色, 当前用户.id, 消息数据
    )
    return {"code": 0, "data": {"messageId": 消息.id}, "message": "消息发送成功"}


@router.post("/conversations/{conversation_id}/read")
async def 标记已读接口(
    conversation_id: int,
    已读数据: 标记已读请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """标记会话中指定消息之前的消息为已读"""
    当前用户, 当前角色 = 当前用户信息
    await 消息服务.标记已读(
        数据库, conversation_id, 当前角色, 当前用户.id,
        已读数据.last_read_message_id
    )
    return {"code": 0, "data": None, "message": "标记已读成功"}
