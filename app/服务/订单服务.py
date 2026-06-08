from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import joinedload
from typing import Optional, List, Tuple
from app.模型.订单 import 订单表, 订单操作日志表, 订单状态枚举
from app.模型.订单项目 import 订单项目表
from app.模型.游戏 import 项目表, 游戏表
from app.模式.订单 import 订单创建, 订单项目创建
from app.工具.订单号生成器 import 生成订单号
from app.工具.价格计算器 import 计算项目价格
from app.核心.加密 import 加解密工具
from app.模型.用户 import 用户表, 打手表


class 订单服务类:
    """订单相关的业务逻辑，包括创建、状态流转、评价等"""

    @staticmethod
    async def 创建订单(
        数据库: AsyncSession,
        用户ID: int,
        订单数据: 订单创建
    ) -> 订单表:
        """创建新订单，包含订单项信息并计算总价"""
        总金额 = Decimal('0.00')
        订单项列表 = []

        for 项目条目 in 订单数据.items:
            项目 = await 数据库.get(项目表, 项目条目.projectId)
            if not 项目:
                raise ValueError(f"项目 {项目条目.projectId} 不存在")

            价格计算结果 = 计算项目价格(项目, 项目条目.quantity)
            订单项 = 订单项目表(
                项目ID=项目.id,
                项目名称=项目.名称,
                数量=价格计算结果['quantity'],
                单价=Decimal(str(价格计算结果['unit_price'])) / 100,
                总价=Decimal(str(价格计算结果['total'])) / 100
            )
            订单项列表.append(订单项)
            总金额 += 订单项.总价

        账号信息密文 = 加解密工具.加密(订单数据.accountInfo) if 订单数据.accountInfo else None

        订单 = 订单表(
            订单号=生成订单号(),
            用户ID=用户ID,
            游戏ID=订单数据.gameId,
            总金额=总金额,
            账号信息密文=账号信息密文,
            需求描述=订单数据.requirements,
            订单项列表=订单项列表
        )
        数据库.add(订单)
        await 数据库.commit()
        await 数据库.refresh(订单)
        return 订单

    @staticmethod
    async def 获取订单池(
        数据库: AsyncSession,
        页码: int = 1,
        每页数量: int = 20,
        排序字段: str = "created_at",
        排序方向: str = "desc",
        查询关键词: Optional[str] = None,
        游戏ID: Optional[int] = None
    ) -> Tuple[List[订单表], int]:
        """获取订单池列表（待审核/待接单的订单），支持分页和筛选"""
        状态条件 = 订单表.状态.in_([订单状态枚举.待审核.value, 订单状态枚举.待支付.value])
        查询条件 = 状态条件

        if 游戏ID:
            查询条件 &= (订单表.游戏ID == 游戏ID)

        查询 = select(订单表).where(查询条件).options(
            joinedload(订单表.游戏),
            joinedload(订单表.订单项列表)
        )

        if 查询关键词:
            查询 = 查询.where(订单表.订单号.like(f"%{查询关键词}%"))

        if 排序字段 == "created_at":
            排序方法 = 订单表.创建时间.desc() if 排序方向 == "desc" else 订单表.创建时间.asc()
        elif 排序字段 == "total_amount":
            排序方法 = 订单表.总金额.desc() if 排序方向 == "desc" else 订单表.总金额.asc()
        else:
            排序方法 = 订单表.创建时间.desc()
        查询 = 查询.order_by(排序方法)

        总记录数查询 = select(func.count()).select_from(订单表).where(查询条件)
        总记录数结果 = await 数据库.execute(总记录数查询)
        总记录数 = 总记录数结果.scalar()

        查询 = 查询.offset((页码 - 1) * 每页数量).limit(每页数量)
        结果 = await 数据库.execute(查询)
        订单列表 = 结果.unique().scalars().all()

        return 订单列表, 总记录数

    @staticmethod
    async def 获取用户订单(
        数据库: AsyncSession,
        用户ID: int,
        角色: str,
        状态过滤: Optional[str] = None,
        页码: int = 1,
        每页数量: int = 20
    ):
        """获取指定用户的订单列表"""
        if 角色 == "user":
            查询 = select(订单表).where(订单表.用户ID == 用户ID)
        else:
            查询 = select(订单表).where(订单表.打手ID == 用户ID)

        if 状态过滤:
            查询 = 查询.where(订单表.状态 == 状态过滤)

        查询 = 查询.order_by(订单表.创建时间.desc()).options(
            joinedload(订单表.游戏),
            joinedload(订单表.订单项列表)
        )

        总记录数查询 = select(func.count()).select_from(订单表)
        if 角色 == "user":
            总记录数查询 = 总记录数查询.where(订单表.用户ID == 用户ID)
        else:
            总记录数查询 = 总记录数查询.where(订单表.打手ID == 用户ID)
        if 状态过滤:
            总记录数查询 = 总记录数查询.where(订单表.状态 == 状态过滤)
        总记录数结果 = await 数据库.execute(总记录数查询)
        总记录数 = 总记录数结果.scalar()

        查询 = 查询.offset((页码 - 1) * 每页数量).limit(每页数量)
        结果 = await 数据库.execute(查询)
        订单列表 = 结果.unique().scalars().all()

        return 订单列表, 总记录数

    @staticmethod
    async def 获取订单详情(
        数据库: AsyncSession,
        订单ID: int,
        当前用户ID: int,
        当前用户角色: str
    ) -> 订单表:
        """获取订单详情，包含游戏、订单项等关联数据"""
        查询 = select(订单表).where(订单表.id == 订单ID).options(
            joinedload(订单表.游戏),
            joinedload(订单表.订单项列表)
        )
        结果 = await 数据库.execute(查询)
        订单 = 结果.unique().scalar_one_or_none()
        if not 订单:
            raise ValueError("订单不存在")
        return 订单

    @staticmethod
    async def 更新订单状态(
        数据库: AsyncSession,
        订单ID: int,
        操作: str,
        备注: Optional[str] = None,
        证据图片: Optional[List[str]] = None
    ) -> 订单表:
        """根据操作类型更新订单状态，并记录操作日志"""
        订单 = await 数据库.get(订单表, 订单ID)
        if not 订单:
            raise ValueError("订单不存在")

        状态变更映射 = {
            "pay": (订单状态枚举.待支付.value, 订单状态枚举.待审核.value),
            "accept": (None, 订单状态枚举.已接单.value),
            "start": (订单状态枚举.已接单.value, 订单状态枚举.进行中.value),
            "submit_review": (订单状态枚举.进行中.value, 订单状态枚举.验收中.value),
            "confirm_complete": (订单状态枚举.验收中.value, 订单状态枚举.已完成.value),
            "cancel": (None, 订单状态枚举.已取消.value),
            "dispute": (None, 订单状态枚举.争议中.value),
            "report_abnormal": (订单状态枚举.进行中.value, 订单状态枚举.异常.value),
        }

        if 操作 not in 状态变更映射:
            raise ValueError(f"未知操作类型: {操作}")

        旧状态, 新状态 = 状态变更映射[操作]
        if 旧状态 and 订单.状态 != 旧状态:
            raise ValueError(f"订单当前状态为 {订单.状态}，不允许执行 {操作} 操作")

        订单.状态 = 新状态
        if 操作 == "submit_review" and 证据图片:
            订单.完成证据 = 证据图片
        if 操作 == "confirm_complete":
            订单.完成时间 = func.now()

        日志 = 订单操作日志表(
            订单ID=订单ID,
            动作=操作,
            操作者类型="system",
            操作者ID=0,
            旧状态=旧状态,
            新状态=新状态,
            备注=备注
        )
        数据库.add(日志)
        await 数据库.commit()
        await 数据库.refresh(订单)
        return 订单

    @staticmethod
    async def 评价订单(
        数据库: AsyncSession,
        订单ID: int,
        角色: str,
        评分: int,
        评价内容: Optional[str] = None
    ) -> 订单表:
        """用户或打手对订单进行评分和评价"""
        订单 = await 数据库.get(订单表, 订单ID)
        if not 订单:
            raise ValueError("订单不存在")

        if 角色 == "user":
            订单.用户评分 = 评分
            订单.用户评价 = 评价内容
        elif 角色 == "handler":
            订单.打手评分 = 评分
            订单.打手评价 = 评价内容

        await 数据库.commit()
        await 数据库.refresh(订单)
        return 订单

    @staticmethod
    async def 删除订单(
        数据库: AsyncSession,
        订单ID: int
    ):
        """删除订单及其关联的订单项和操作日志"""
        订单 = await 数据库.get(订单表, 订单ID)
        if not 订单:
            raise ValueError("订单不存在")
        await 数据库.delete(订单)
        await 数据库.commit()

    @staticmethod
    async def 取消订单(
        数据库: AsyncSession,
        订单ID: int
    ) -> 订单表:
        """取消订单（仅待支付和待审核状态的订单可取消）"""
        订单 = await 数据库.get(订单表, 订单ID)
        if not 订单:
            raise ValueError("订单不存在")
        if 订单.状态 not in [订单状态枚举.待支付.value, 订单状态枚举.待审核.value]:
            raise ValueError("当前状态不允许取消")

        订单.状态 = 订单状态枚举.已取消.value
        await 数据库.commit()
        await 数据库.refresh(订单)
        return 订单


    @staticmethod
    async def 创建匿名订单(
        数据库: AsyncSession,
        订单数据: 订单创建
    ) -> 订单表:
        """创建匿名订单，自动创建匿名用户"""
        import uuid
        from passlib.context import CryptContext
        
        匿名邮箱 = f"anonymous_{uuid.uuid4().hex[:16]}@anon.fashiye.cn"
        匿名用户名 = f"匿名用户_{uuid.uuid4().hex[:8]}"
        
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        密码哈希 = pwd_context.hash("anonymous_random_password_123")
        
        匿名用户 = 用户表(
            邮箱=匿名邮箱,
            用户名=匿名用户名,
            密码哈希=密码哈希
        )
        数据库.add(匿名用户)
        await 数据库.flush()
        
        return await 订单服务类.创建订单(数据库, 匿名用户.id, 订单数据)

    @staticmethod
    async def 根据订单号查询订单(
        数据库: AsyncSession,
        订单号: str
    ) -> 订单表:
        """根据订单号查询订单详情"""
        查询 = select(订单表).where(订单表.订单号 == 订单号).options(
            joinedload(订单表.游戏),
            joinedload(订单表.订单项列表),
            joinedload(订单表.打手)
        )
        结果 = await 数据库.execute(查询)
        订单 = 结果.unique().scalar_one_or_none()
        if not 订单:
            raise ValueError("订单不存在")
        return 订单


订单服务 = 订单服务类()
