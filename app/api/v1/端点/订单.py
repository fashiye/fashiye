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
from app.核心.加密 import 加解密工具

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

    # 安全：排序参数白名单映射，防止 SQL 注入
    排序白名单: dict[str, tuple[str, str]] = {
        "latest": ("created_at", "desc"),
        "price_asc": ("total_amount", "asc"),
        "price_desc": ("total_amount", "desc"),
    }
    if 排序 not in 排序白名单:
        raise 业务逻辑错误(f"不支持的排序方式: {排序}")
    排序字段, 排序方向 = 排序白名单[排序]

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

    # 安全：单条 JOIN 聚合查询代替 N+1 循环
    统计查询 = (
        select(
            游戏表.id,
            游戏表.名称,
            func.count(订单表.id).label("order_count"),
            func.min(订单表.总金额).label("min_price"),
            func.max(订单表.总金额).label("max_price"),
        )
        .join(订单表, 订单表.游戏ID == 游戏表.id)
        .where(订单表.状态.in_([订单状态枚举.待审核.value, 订单状态枚举.待支付.value]))
        .group_by(游戏表.id, 游戏表.名称)
        .order_by(游戏表.名称)
    )
    统计结果集 = await 数据库.execute(统计查询)
    统计行 = 统计结果集.all()

    统计结果 = [
        {
            "gameId": 行.id,
            "gameName": 行.名称,
            "orderCount": 行.order_count,
            "minPrice": str(行.min_price) if 行.min_price else "0",
            "maxPrice": str(行.max_price) if 行.max_price else "0",
        }
        for 行 in 统计行
    ]

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


@router.get("/orders/pending-review")
async def 获取待审核订单接口(
    页码: int = Query(1, ge=1),
    每页数量: int = Query(20, ge=1, le=100),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取待审核订单列表（仅管理员，状态为 pending_review）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["super", "operator"]:
        raise 业务逻辑错误("仅管理员可查看待审核订单")

    订单列表, 总记录数 = await 订单服务.获取待审核订单(数据库, 页码, 每页数量)

    待审核数据 = []
    for 订单 in 订单列表:
        游戏名称 = 订单.游戏.名称 if 订单.游戏 else ""
        项目摘要 = ""
        if 订单.订单项列表:
            项目摘要 = ", ".join([f"{项.项目名称} x{项.数量}" for 项 in 订单.订单项列表])

        待审核数据.append({
            "id": 订单.id,
            "orderNo": 订单.订单号,
            "userId": 订单.用户ID,
            "gameName": 游戏名称,
            "itemSummary": 项目摘要,
            "totalAmount": str(订单.总金额),
            "requirements": 订单.需求描述 or "",
            "status": 订单.状态,
            "createdAt": 订单.创建时间.isoformat() if 订单.创建时间 else None
        })

    return {
        "code": 0,
        "data": 待审核数据,
        "total": 总记录数,
        "message": "获取待审核订单成功"
    }


@router.get("/orders/all")
async def 获取所有订单接口(
    状态过滤: Optional[str] = Query(None, description="按状态筛选"),
    页码: int = Query(1, ge=1),
    每页数量: int = Query(20, ge=1, le=200),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取所有订单列表（仅管理员）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["super", "operator"]:
        raise 业务逻辑错误("仅管理员可查看所有订单")

    订单列表, 总记录数 = await 订单服务.获取所有订单(数据库, 状态过滤, 页码, 每页数量)

    return {
        "code": 0,
        "data": 订单列表,
        "total": 总记录数,
        "message": "获取所有订单成功"
    }


@router.get("/orders/my")
async def 获取我的订单接口(
    状态过滤: Optional[str] = Query(None, alias="status"),
    页码: int = Query(1, alias="page"),
    每页数量: int = Query(20, alias="size"),
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

        # 安全：匿名查询不返回账号信息，防止订单号泄露游戏账号密码
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
                accountInfo=None,
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
    except Exception as e:
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

        # 安全：仅订单所有者、接单打手、管理员可查看解密后的账号信息
        当前用户ID = 当前用户信息[0].id if 当前用户信息 else None
        当前角色 = 当前用户信息[1] if 当前用户信息 else None
        可否查看账号 = False
        if 当前角色 == "admin":
            可否查看账号 = True
        elif 当前角色 == "user" and 当前用户ID == 订单.用户ID:
            可否查看账号 = True
        elif 当前角色 == "handler" and 当前用户ID == 订单.打手ID:
            可否查看账号 = True
        解密后账号 = 加解密工具.解密(订单.账号信息密文) if (订单.账号信息密文 and 可否查看账号) else None

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
                accountInfo=解密后账号,
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
    except Exception as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/{order_id}/accept")
async def 接单接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """打手接单，将订单状态改为已接单"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["handler", "super", "operator"]:
        raise 业务逻辑错误("仅打手和管理员可以接单")

    try:
        订单 = await 订单服务.接单(数据库, order_id, 当前用户.id)
        return {"code": 0, "data": {"orderId": 订单.id, "status": 订单.状态}, "message": "接单成功"}
    except Exception as e:
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

    # 安全：验证操作者与订单的关系
    订单查询 = select(订单表).where(订单表.id == order_id)
    订单结果 = await 数据库.execute(订单查询)
    订单 = 订单结果.scalar_one_or_none()
    if not 订单:
        raise 业务逻辑错误("订单不存在")
    if 当前角色 == "user" and 订单.用户ID != 当前用户.id:
        raise 业务逻辑错误("您无权操作此订单")
    if 当前角色 == "handler" and 订单.打手ID != 当前用户.id:
        raise 业务逻辑错误("您无权操作此订单")

    try:
        # 数据库 operator_type 列允许值：user、handler、admin
        操作者类型映射: dict[str, str] = {"user": "user", "handler": "handler", "super": "admin", "operator": "admin"}
        操作者类型 = 操作者类型映射.get(当前角色, "admin")

        订单 = await 订单服务.更新订单状态(
            数据库, order_id, 状态更新.action,
            状态更新.remark, 状态更新.completionProof,
            操作者类型=操作者类型, 操作者ID=当前用户.id
        )
        return {"code": 0, "data": {"orderId": 订单.id, "status": 订单.状态}, "message": "订单状态更新成功"}
    except Exception as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/{order_id}/approve")
async def 批准订单接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """管理员批准待审核订单"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["super", "operator"]:
        raise 业务逻辑错误("仅管理员可以批准订单")

    try:
        订单 = await 订单服务.批准订单(数据库, order_id)
        return {"code": 0, "data": {"orderId": 订单.id}, "message": "订单已批准"}
    except Exception as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/{order_id}/reject")
async def 拒绝订单接口(
    order_id: int,
    remark: str = Query(""),
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """管理员拒绝待审核订单（将状态改为已取消）"""
    当前用户, 当前角色 = 当前用户信息
    if 当前角色 not in ["super", "operator"]:
        raise 业务逻辑错误("仅管理员可以拒绝订单")

    try:
        订单 = await 订单服务.拒绝订单(数据库, order_id, remark or None)
        return {"code": 0, "data": {"orderId": 订单.id}, "message": "订单已拒绝"}
    except Exception as e:
        raise 业务逻辑错误(str(e))


@router.get("/orders/{order_id}/logs")
async def 获取订单日志接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """获取订单的操作日志（仅订单参与者和管理员可查看）"""
    当前用户, 当前角色 = 当前用户信息

    # 安全：验证操作者与订单的关系
    订单查询 = select(订单表).where(订单表.id == order_id)
    订单结果 = await 数据库.execute(订单查询)
    订单 = 订单结果.scalar_one_or_none()
    if not 订单:
        raise 业务逻辑错误("订单不存在")
    if 当前角色 not in ("super", "operator", "admin"):
        if (当前角色 == "user" and 订单.用户ID != 当前用户.id) or \
           (当前角色 == "handler" and 订单.打手ID != 当前用户.id):
            raise 业务逻辑错误("您无权查看此订单日志")

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

    try:
        订单 = await 订单服务.评价订单(
            数据库, order_id, 评价数据.role,
            评价数据.rating, 评价数据.comment
        )
        return {"code": 0, "data": {"orderId": 订单.id}, "message": "评价成功"}
    except Exception as e:
        raise 业务逻辑错误(str(e))


@router.post("/orders/{order_id}/cancel")
async def 取消订单接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户)
):
    """取消订单（仅待支付和待审核状态可取消）"""
    当前用户, 当前角色 = 当前用户信息

    # 安全：验证操作者与订单的关系
    订单查询 = select(订单表).where(订单表.id == order_id)
    订单结果 = await 数据库.execute(订单查询)
    订单 = 订单结果.scalar_one_or_none()
    if not 订单:
        raise 业务逻辑错误("订单不存在")
    if 当前角色 == "user" and 订单.用户ID != 当前用户.id:
        raise 业务逻辑错误("您无权取消此订单")
    if 当前角色 == "handler" and 订单.打手ID != 当前用户.id:
        raise 业务逻辑错误("您无权取消此订单")

    try:
        订单 = await 订单服务.取消订单(数据库, order_id)
        return {"code": 0, "data": None, "message": "订单取消成功"}
    except Exception as e:
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
    except Exception as e:
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
    except Exception as e:
        raise 业务逻辑错误(str(e))
