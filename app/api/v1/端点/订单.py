from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.数据库.会话 import 获取数据库会话
from app.模式.订单 import (
    订单响应, 订单项目响应, 订单池项目, 订单创建, 订单状态更新, 订单评价
)
from app.服务.订单服务 import 订单服务
from app.api.依赖.认证 import 获取当前用户, 获取当前用户可选
from app.模型.订单 import 订单表, 订单操作日志表, 订单状态枚举
from app.模型.订单项目 import 订单项目表
from app.模型.游戏 import 游戏表
from app.核心.异常 import 业务逻辑错误
from typing import Optional, List
from decimal import Decimal

router = APIRouter()


@router.post("/orders")
async def 创建订单接口(
    订单数据: 订单创建,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """创建新订单（需要用户身份认证）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 != "user":
        raise 业务逻辑错误("仅用户角色可以创建订单")

    订单 = await 订单服务.创建订单(数据库, 当前用户.id, 订单数据)
    return {"code": 0, "data": {"orderId": 订单.id}, "message": "订单创建成功"}


@router.get("/orders/pool")
async def 获取订单池接口(
    页码: int = Query(1, ge=1),
    每页数量: int = Query(20, ge=1, le=100),
    排序: str = Query("latest", description="排序: latest/price_asc/price_desc"),
    游戏ID: Optional[int] = Query(None, description="按游戏筛选"),
    查询关键词: Optional[str] = Query(None, description="搜索关键词"),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """查看订单池 - 获取所有可接单的订单（打手和管理员可查看）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["handler", "super", "operator"]:
        raise 业务逻辑错误("仅打手和管理员可以查看订单池")

    排序字段 = "created_at"
    排序方向 = "desc"
    if 排序 == "price_asc":
        排序字段 = "total_amount"
        排序方向 = "asc"
    elif 排序 == "price_desc":
        排序字段 = "total_amount"
        排序方向 = "desc"

    订单列表, 总记录数 = await 订单服务.获取订单池(
        数据库, 页码, 每页数量, 排序字段, 排序方向, 查询关键词, 游戏ID
    )

    订单池数据 = []
    for 订单 in 订单列表:
        游戏名称 = 订单.游戏.名称 if 订单.游戏 else ""
        项目摘要 = ""
        if 订单.订单项列表:
            项目摘要 = ", ".join([f"{项.项目名称} x{项.数量}" for 项 in 订单.订单项列表])

        订单池数据.append(订单池项目(
            id=订单.id,
            orderNo=订单.订单号,
            gameName=游戏名称,
            itemSummary=项目摘要,
                totalAmount=订单.总金额,
            requirements=订单.需求描述,
            createdAt=订单.创建时间
        ))

    return {
        "code": 0,
        "data": {
            "items": 订单池数据,
            "total": 总记录数,
            "page": 页码,
            "pageSize": 每页数量
        },
        "message": "获取订单池成功"
    }


@router.get("/orders/pool/statistics")
async def 获取订单池统计接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取订单池统计信息 - 各游戏待接单数量、价格范围"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["handler", "super", "operator"]:
        raise 业务逻辑错误("权限不足")

    游戏查询 = select(游戏表).order_by(游戏表.名称)
    游戏结果 = await 数据库.execute(游戏查询)
    游戏列表 = 游戏结果.scalars().all()

    统计结果 = []
    for 游戏 in 游戏列表:
        数量查询 = select(func.count()).select_from(订单表).where(
            订单表.游戏ID == 游戏.id,
            订单表.状态.in_([订单状态枚举.待审核.value, 订单状态枚举.待支付.value])
        )
        数量结果 = await 数据库.execute(数量查询)
        订单数量 = 数量结果.scalar()

        if 订单数量 > 0:
            价格查询 = select(
                func.min(订单表.总金额).label("min_price"),
                func.max(订单表.总金额).label("max_price")
            ).where(
                订单表.游戏ID == 游戏.id,
                订单表.状态.in_([订单状态枚举.待审核.value, 订单状态枚举.待支付.value])
            )
            价格结果 = await 数据库.execute(价格查询)
            价格信息 = 价格结果.one()

            统计结果.append({
                "gameId": 游戏.id,
                "gameName": 游戏.名称,
                "orderCount": 订单数量,
                "minPrice": float(价格信息.min_price) if 价格信息.min_price else 0,
                "maxPrice": float(价格信息.max_price) if 价格信息.max_price else 0
            })

    return {
        "code": 0,
        "data": 统计结果,
        "message": "获取统计成功"
    }


@router.get("/orders/pool/games")
async def 获取订单池游戏列表接口(
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取有可接单订单的游戏列表（用于筛选）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["handler", "super", "operator"]:
        raise 业务逻辑错误("权限不足")

    查询 = (
        select(游戏表)
        .join(订单表, 订单表.游戏ID == 游戏表.id)
        .where(订单表.状态.in_([订单状态枚举.待审核.value, 订单状态枚举.待支付.value]))
        .distinct()
        .order_by(游戏表.名称)
    )
    结果 = await 数据库.execute(查询)
    游戏列表 = 结果.scalars().all()

    return {
        "code": 0,
        "data": [{"id": 游戏.id, "name": 游戏.名称} for 游戏 in 游戏列表],
        "message": "获取成功"
    }


@router.get("/orders/my")
async def 获取我的订单接口(
    状态过滤: Optional[str] = None,
    页码: int = 1,
    每页数量: int = 20,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取当前用户的订单列表（根据角色自动区分用户订单/打手订单）"""
    当前用户, 当前角色 = 当前用户信息
    订单列表, 总记录数 = await 订单服务.获取用户订单(
        数据库, 当前用户.id, 当前角色, 状态过滤, 页码, 每页数量
    )
    return {
        "code": 0,
        "data": 订单列表,
        "total": 总记录数,
        "message": "获取订单列表成功"
    }


@router.get("/orders/lookup/{order_no}")
async def 根据订单号查询订单接口(
    order_no: str,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """根据订单号查询订单详情（无需登录，用于凭据查询）"""
    try:
        订单 = await 订单服务.根据订单号查询订单(数据库, order_no)
        游戏名称 = 订单.游戏.名称 if 订单.游戏 else ""
        打手名称 = 订单.打手.用户名 if 订单.打手 else ""
        
        return {
            "code": 0,
            "data": 订单响应(
                id=订单.id,
                orderNo=订单.订单号,
                userId=订单.用户ID,
                gameId=订单.游戏ID,
                gameName=游戏名称,
                totalAmount=订单.总金额,
                status=订单.状态,
                handlerId=订单.打手ID,
                handlerName=打手名称,
                accountInfo=订单.账号信息密文,
                requirements=订单.需求描述,
                createdAt=订单.创建时间,
                updatedAt=订单.更新时间,
                items=[订单项目响应(
                    id=项.id,
                    projectId=项.项目ID,
                    projectName=项.项目名称,
                    quantity=项.数量,
                    unitPrice=项.单价,
                    totalPrice=项.总价
                ) for 项 in (订单.订单项列表 or [])]
            ),
            "message": "获取订单详情成功"
        }
    except ValueError as e:
        raise 业务逻辑错误(str(e))


@router.get("/orders/{order_id}")
async def 获取订单详情接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple | None = Depends(获取当前用户可选)
):
    """获取订单详细信息（支持登录和匿名查询）"""
    try:
        订单 = await 订单服务.获取订单详情(数据库, order_id, 当前用户信息[0].id if 当前用户信息 else None, 当前用户信息[1] if 当前用户信息 else None)
        游戏名称 = 订单.游戏.名称 if 订单.游戏 else ""

        return {
            "code": 0,
            "data": 订单响应(
                id=订单.id,
                orderNo=订单.订单号,
                userId=订单.用户ID,
                gameId=订单.游戏ID,
                gameName=游戏名称,
                totalAmount=订单.总金额,
                status=订单.状态,
                handlerId=订单.打手ID,
                accountInfo=订单.账号信息密文,
                requirements=订单.需求描述,
                createdAt=订单.创建时间,
                updatedAt=订单.更新时间,
                items=[订单项目响应(
                    id=项.id,
                    projectId=项.项目ID,
                    projectName=项.项目名称,
                    quantity=项.数量,
                    unitPrice=项.单价,
                    totalPrice=项.总价
                ) for 项 in (订单.订单项列表 or [])]
            ),
            "message": "获取订单详情成功"
        }
    except ValueError as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/{order_id}/status")
async def 更新订单状态接口(
    order_id: int,
    状态更新: 订单状态更新,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """根据操作类型更新订单状态（支付、接单、开始、提交验收、确认完成、取消、争议、异常报告）"""
    当前用户, 当前角色 = 当前用户信息
    try:
        订单 = await 订单服务.更新订单状态(
            数据库, order_id, 状态更新.action,
            状态更新.remark, 状态更新.completionProof
        )
        return {"code": 0, "data": {"orderId": 订单.id, "status": 订单.状态}, "message": "订单状态更新成功"}
    except ValueError as e:
        raise 业务逻辑错误(str(e))


@router.get("/orders/{order_id}/logs")
async def 获取订单日志接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取订单的操作日志"""
    查询 = select(订单操作日志表).where(订单操作日志表.订单ID == order_id).order_by(订单操作日志表.操作时间.desc())
    结果 = await 数据库.execute(查询)
    日志列表 = 结果.scalars().all()
    return {"code": 0, "data": 日志列表, "message": "获取日志成功"}


@router.post("/orders/{order_id}/rate")
async def 评价订单接口(
    order_id: int,
    评价数据: 订单评价,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """对订单进行评分和评价（用户和打手都可评价）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 != 评价数据.role:
        raise 业务逻辑错误("角色不匹配")

    try:
        订单 = await 订单服务.评价订单(
            数据库, order_id, 评价数据.role,
            评价数据.rating, 评价数据.comment
        )
        return {"code": 0, "data": {"orderId": 订单.id}, "message": "评价成功"}
    except ValueError as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/{order_id}/cancel")
async def 取消订单接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """取消订单（仅待支付和待审核状态可取消）"""
    当前用户, 当前角色 = 当前用户信息
    try:
        订单 = await 订单服务.取消订单(数据库, order_id)
        return {"code": 0, "data": None, "message": "订单取消成功"}
    except ValueError as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/anonymous")
async def 创建匿名订单接口(
    订单数据: 订单创建,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """创建匿名订单（无需登录）"""
    try:
        订单 = await 订单服务.创建匿名订单(数据库, 订单数据)
        return {"code": 0, "data": {"orderId": 订单.id, "orderNo": 订单.订单号}, "message": "订单创建成功"}
    except ValueError as e:
        raise 业务逻辑错误(str(e))


@router.delete("/orders/{order_id}")
async def 删除订单接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """删除订单（管理员权限）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["super", "operator"]:
        raise 业务逻辑错误("权限不足")
    try:
        await 订单服务.删除订单(数据库, order_id)
        return {"code": 0, "data": None, "message": "订单删除成功"}
    except ValueError as e:
        raise 业务逻辑错误(str(e))
