from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, case, and_
from app.模型.消息 import 会话表, 消息表, 消息阅读状态表
from app.模式.消息 import 消息创建, 标记已读请求
from typing import Optional, List


class 消息服务类:
    """消息和会话相关的业务逻辑"""

    @staticmethod
    async def 创建会话(
        数据库: AsyncSession,
        发起方类型: str,
        发起方ID: int,
        对方类型: str,
        对方ID: int,
        会话类型: str = "user_handler",
        订单ID: Optional[int] = None
    ) -> 会话表:
        """
        创建新会话或返回已有会话。先检查是否已存在，避免重复创建。

        传入：
            数据库: 异步数据库会话
            发起方类型: 发起方角色（user/handler/admin）
            发起方ID: 发起方用户ID
            对方类型: 对方角色（user/handler/admin）
            对方ID: 对方用户ID
            会话类型: 会话类型，默认 user_handler
            订单ID: 可选的关联订单ID
        作用：
            1. 先查是否已有相同双方的会话
            2. 若有则直接返回，若无则创建新会话
        传出：会话表对象
        """
        from datetime import datetime

        # 检查是否已有会话
        已有会话查询 = select(会话表).where(
            and_(
                会话表.参与方A类型 == 发起方类型,
                会话表.参与方AID == 发起方ID,
                会话表.参与方B类型 == 对方类型,
                会话表.参与方BID == 对方ID,
            )
        )
        结果 = await 数据库.execute(已有会话查询)
        已有会话 = 结果.scalar_one_or_none()

        if not 已有会话:
            # 再查反向
            已有会话查询 = select(会话表).where(
                and_(
                    会话表.参与方A类型 == 对方类型,
                    会话表.参与方AID == 对方ID,
                    会话表.参与方B类型 == 发起方类型,
                    会话表.参与方BID == 发起方ID,
                )
            )
            结果 = await 数据库.execute(已有会话查询)
            已有会话 = 结果.scalar_one_or_none()

        if 已有会话:
            return 已有会话

        # 创建新会话
        新会话 = 会话表(
            类型=会话类型,
            参与方A类型=发起方类型,
            参与方AID=发起方ID,
            参与方B类型=对方类型,
            参与方BID=对方ID,
            创建时间=datetime.now(),
        )
        数据库.add(新会话)
        await 数据库.commit()
        await 数据库.refresh(新会话)
        return 新会话

    @staticmethod
    async def 获取会话列表(
        数据库: AsyncSession,
        用户类型: str,
        用户ID: int,
        页码: int = 1,
        每页数量: int = 20
    ) -> List[会话表]:
        """
        获取用户的会话列表，按最新消息时间倒序排列

        Args:
            数据库: 异步数据库会话
            用户类型: 用户角色类型（user/handler）
            用户ID: 用户ID
            页码: 当前页码（从1开始）
            每页数量: 每页显示条数

        Returns:
            会话对象列表
        """
        查询 = select(会话表).where(
            (会话表.参与方A类型 == 用户类型) & (会话表.参与方AID == 用户ID) |
            (会话表.参与方B类型 == 用户类型) & (会话表.参与方BID == 用户ID)
        )
        查询 = 查询.order_by(
            case(
                (会话表.最后消息时间 == None, 1),
                else_=0
            ).asc(),
            会话表.最后消息时间.desc()
        )
        查询 = 查询.offset((页码 - 1) * 每页数量).limit(每页数量)

        结果 = await 数据库.execute(查询)
        会话列表 = 结果.scalars().all()
        return 会话列表

    @staticmethod
    async def 获取消息列表(
        数据库: AsyncSession,
        会话ID: int,
        起始消息ID: Optional[int] = None,
        限制数量: int = 20
    ) -> List[消息表]:
        """
        获取指定会话的消息列表（分页、从新到旧）

        Args:
            数据库: 异步数据库会话
            会话ID: 会话ID
            起始消息ID: 起始消息ID（用于加载更早的消息）
            限制数量: 返回消息的最大数量

        Returns:
            消息对象列表（按时间正序排列）
        """
        查询 = select(消息表).where(消息表.会话ID == 会话ID)

        if 起始消息ID:
            查询 = 查询.where(消息表.id < 起始消息ID)

        查询 = 查询.order_by(消息表.发送时间.desc())
        查询 = 查询.limit(限制数量)

        结果 = await 数据库.execute(查询)
        消息列表 = 结果.scalars().all()

        return list(reversed(消息列表))

    @staticmethod
    async def 发送消息(
        数据库: AsyncSession,
        会话ID: int,
        发送者类型: str,
        发送者ID: int,
        消息数据: 消息创建
    ) -> 消息表:
        """
        发送新消息并更新会话的最后消息信息

        Args:
            数据库: 异步数据库会话
            会话ID: 目标会话ID
            发送者类型: 发送者角色类型
            发送者ID: 发送者用户ID
            消息数据: 消息内容及附件信息

        Returns:
            创建后的消息对象
        """
        消息 = 消息表(
            会话ID=会话ID,
            发送者类型=发送者类型,
            发送者ID=发送者ID,
            内容=消息数据.content,
            内容类型=消息数据.contentType,
            附件=消息数据.attachment,
            订单ID=消息数据.orderId
        )
        数据库.add(消息)

        await 数据库.execute(
            update(会话表)
            .where(会话表.id == 会话ID)
            .values(
                最后消息=消息数据.content,
                最后消息时间=func.now()
            )
        )

        await 数据库.commit()
        await 数据库.refresh(消息)
        return 消息

    @staticmethod
    async def 标记已读(
        数据库: AsyncSession,
        会话ID: int,
        参与方类型: str,
        参与方ID: int,
        最后阅读消息ID: int
    ) -> 消息阅读状态表:
        """
        将会话中指定参与方的已读标记更新到指定消息

        Args:
            数据库: 异步数据库会话
            会话ID: 会话ID
            参与方类型: 参与方角色类型
            参与方ID: 参与方用户ID
            最后阅读消息ID: 最后一条已读消息的ID

        Returns:
            更新后的阅读状态记录
        """
        现有结果 = await 数据库.execute(
            select(消息阅读状态表).where(
                消息阅读状态表.会话ID == 会话ID,
                消息阅读状态表.参与方类型 == 参与方类型,
                消息阅读状态表.参与方ID == 参与方ID
            ).order_by(消息阅读状态表.id.desc()).limit(1)
        )
        阅读状态 = 现有结果.scalar_one_or_none()

        if 阅读状态:
            阅读状态.最后阅读消息ID = 最后阅读消息ID
        else:
            阅读状态 = 消息阅读状态表(
                会话ID=会话ID,
                参与方类型=参与方类型,
                参与方ID=参与方ID,
                最后阅读消息ID=最后阅读消息ID
            )
            数据库.add(阅读状态)

        await 数据库.commit()
        return 阅读状态

    @staticmethod
    async def 获取未读数量(
        数据库: AsyncSession,
        会话ID: int,
        参与方类型: str,
        参与方ID: int
    ) -> int:
        """
        计算指定参与方在会话中的未读消息数量

        Args:
            数据库: 异步数据库会话
            会话ID: 会话ID
            参与方类型: 参与方角色类型
            参与方ID: 参与方用户ID

        Returns:
            未读消息数量
        """
        阅读状态结果 = await 数据库.execute(
            select(消息阅读状态表).where(
                消息阅读状态表.会话ID == 会话ID,
                消息阅读状态表.参与方类型 == 参与方类型,
                消息阅读状态表.参与方ID == 参与方ID
            ).order_by(消息阅读状态表.id.desc()).limit(1)
        )
        阅读状态 = 阅读状态结果.scalar_one_or_none()

        if not 阅读状态 or not 阅读状态.最后阅读消息ID:
            查询 = select(func.count(消息表.id)).where(消息表.会话ID == 会话ID)
            结果 = await 数据库.execute(查询)
            return 结果.scalar()

        查询 = select(func.count(消息表.id)).where(
            消息表.会话ID == 会话ID,
            消息表.id > 阅读状态.最后阅读消息ID
        )
        结果 = await 数据库.execute(查询)
        return 结果.scalar()


消息服务 = 消息服务类()
