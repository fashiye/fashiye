from typing import Optional                                   # 可选类型注解
from fastapi import APIRouter, Depends, HTTPException, Request  # FastAPI 路由、依赖注入、HTTP 异常、请求对象
from pydantic import BaseModel, Field                           # 数据验证模型和字段定义
from sqlalchemy.ext.asyncio import AsyncSession                 # 异步数据库会话
from sqlalchemy import select                                   # 查询构造器

from app.数据库.会话 import 获取数据库会话        # 获取异步数据库会话依赖
from app.api.依赖.认证 import 获取当前用户           # 获取当前登录用户依赖
from app.模型.订单 import 订单表                    # 订单数据库表模型
from app.模型.支付 import 支付记录表                 # 支付记录数据库表模型
from app.模型.用户 import 用户表                    # 用户数据库表模型
from app.核心.异常 import 业务逻辑错误               # 业务逻辑异常类
from app.服务.支付服务 import 支付服务对象            # 支付服务单例对象


class 发起支付请求(BaseModel):
    """
    发起支付请求的数据模型。

    传入：
        订单ID：内部订单 ID（必填）
        支付方式：支付方式（可选，iaitouzi 统一支付页面选择）
        联系方式：用户联系方式（必填，用于订单找回）
        重定向地址：支付成功后前端跳转地址（可选，默认订单详情页）
    作用：
        定义支付请求的入参结构和验证规则
    """
    订单ID: int = Field(..., description="内部订单 ID")
    支付方式: str = Field("", description="支付方式（保留字段）")
    联系方式: str = Field(..., min_length=1, description="用户联系方式，用于订单找回")
    重定向地址: Optional[str] = Field(None, description="支付成功后重定向的前端地址")


router = APIRouter()


@router.post("/payment/create")
async def 发起支付接口(
    请求数据: 发起支付请求,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(获取当前用户),
):
    """
    发起支付 - 为登录用户的订单创建 iaitouzi 支付订单。

    传入：
        请求数据：包含订单 ID、联系方式、重定向地址等
        数据库：异步数据库会话
        当前用户信息：(用户对象, 角色) 元组
    作用：
        1. 验证订单存在且属于当前用户，状态允许支付
        2. 调用 iaitouzi 创建支付订单并获取支付链接
        3. 保存支付记录到本地数据库
    传出：
        包含 paymentUrl（支付跳转链接）的响应
    """
    # 调用库函数：解包当前用户信息
    # 传入：当前用户信息元组（用户对象, 角色字符串）
    # 作用：从认证依赖的返回结果中提取用户对象
    # 传出：当前用户 ORM 对象
    当前用户, _ = 当前用户信息
    订单查询 = select(订单表).where(
        订单表.id == 请求数据.订单ID,
        订单表.用户ID == 当前用户.id,
    )
    订单结果 = await 数据库.execute(订单查询)
    订单 = 订单结果.scalar_one_or_none()

    if not 订单:
        raise 业务逻辑错误("订单不存在")

    if 订单.状态 not in ["pending", "pending_review"]:
        raise 业务逻辑错误(f"当前订单状态 ({订单.状态}) 不允许支付")

    try:
        # 调用库函数：创建 iaitouzi 支付订单
        # 传入：数据库会话、内部订单对象、联系方式、支付方式、重定向地址
        # 作用：后端 POST 到 iaitouzi（带上 type 指定支付方式），
        #       解析响应提取真实支付 URL，然后访问支付页面捞取二维码图片。
        #       内部自动创建支付记录并 commit。
        # 传出：包含 paymentUrl（支付跳转链接）、qrCodeImage（二维码 base64 图片）、
        #       formData（表单参数）、paymentOrderId 的字典
        支付信息 = await 支付服务对象.创建支付订单(
            数据库, 订单, 请求数据.联系方式,
            支付方式=请求数据.支付方式,
            重定向地址=请求数据.重定向地址 or f"http://localhost:5173/order-detail/{请求数据.订单ID}",
        )

        return {
            "code": 0,
            "data": {
                "paymentUrl": 支付信息["paymentUrl"],
                "qrCodeImage": 支付信息.get("qrCodeImage"),
                "formData": 支付信息.get("formData", {}),
                "paymentOrderId": 支付信息["paymentOrderId"],
            },
            "message": "支付订单创建成功",
        }

    except ValueError as e:
        await 数据库.rollback()
        raise 业务逻辑错误(str(e))


@router.post("/payment/anonymous/create")
async def 匿名发起支付接口(
    请求数据: 发起支付请求,
    数据库: AsyncSession = Depends(获取数据库会话),
):
    """
    匿名发起支付 - 为匿名订单创建 iaitouzi 支付订单（无需登录）。

    传入：
        请求数据：包含订单 ID、联系方式、重定向地址等
        数据库：异步数据库会话
    作用：
        1. 验证匿名订单存在且状态为待支付
        2. 后端 POST 到 iaitouzi，跟随重定向，从 HTML 提取真实支付表单
        3. 前端根据 formData 决定直接跳转或表单提交到真实支付页面
    传出：
        包含 paymentUrl、formData 的响应
    """
    # 验证订单存在且无需登录（只要订单存在且可支付即可）
    订单查询 = select(订单表).where(订单表.id == 请求数据.订单ID)
    订单结果 = await 数据库.execute(订单查询)
    订单 = 订单结果.scalar_one_or_none()

    if not 订单:
        raise 业务逻辑错误("订单不存在")

    if 订单.状态 not in ["pending", "pending_review"]:
        raise 业务逻辑错误(f"当前订单状态 ({订单.状态}) 不允许支付")

    try:
        # 调用库函数：创建 iaitouzi 支付订单
        # 传入：数据库会话、内部订单对象、联系方式、支付方式、重定向地址
        # 作用：后端 POST 到 iaitouzi（带上 type 指定支付方式），
        #       解析响应提取真实支付 URL，然后访问支付页面捞取二维码图片。
        #       内部自动创建支付记录并 commit。
        # 传出：包含 paymentUrl（支付跳转链接）、qrCodeImage（二维码 base64 图片）、
        #       formData（表单参数）、paymentOrderId 的字典
        支付信息 = await 支付服务对象.创建支付订单(
            数据库, 订单, 请求数据.联系方式,
            支付方式=请求数据.支付方式,
            重定向地址=请求数据.重定向地址 or f"http://localhost:5173/order-detail/{请求数据.订单ID}",
        )

        return {
            "code": 0,
            "data": {
                "paymentUrl": 支付信息["paymentUrl"],
                "qrCodeImage": 支付信息.get("qrCodeImage"),
                "formData": 支付信息.get("formData", {}),
                "paymentOrderId": 支付信息["paymentOrderId"],
            },
            "message": "支付订单创建成功",
        }

    except ValueError as e:
        await 数据库.rollback()
        raise 业务逻辑错误(str(e))


@router.post("/payment/callback")
async def 支付回调接口(
    请求: Request,
    数据库: AsyncSession = Depends(获取数据库会话),
):
    """
    iaitouzi 支付结果回调通知接口（Webhook）。

    传入：
        请求：iaitouzi 平台 POST 发送的表单数据
    作用：
        1. 接收 iaitouzi 的支付结果通知
        2. 验证回调签名
        3. 更新支付记录和订单状态
    传出：
        "success" 字符串（iaitouzi 期望的响应）或 "fail"
    """
    try:
        # 调用库函数：从请求中获取表单数据
        # 传入：无
        # 作用：解析 POST 表单请求体为字典
        # 传出：dict[str, str] 类型的表单数据
        表单数据 = dict(await 请求.form())

        # 调用服务方法：处理支付回调
        # 传入：iaitouzi 回调表单数据、数据库会话
        # 作用：验证签名、更新本地支付记录和订单状态
        # 传出：True（成功）或异常（失败）
        await 支付服务对象.处理支付回调(表单数据, 数据库)

        # iaitouzi 期望收到 "success" 文本响应
        return "success"

    except Exception as e:
        # 调用库函数：记录异常日志
        # 传入：错误消息
        # 作用：将回调处理失败记录到日志文件
        # 传出：无返回值
        import logging
        logging.getLogger(__name__).error(f"支付回调处理失败: {e}")
        return "fail"


@router.get("/payment/status/{order_id}")
async def 查询支付状态接口(
    order_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
):
    """
    查询支付状态 - 查询本地支付记录状态。

    传入：
        order_id：内部订单 ID（路径参数）
        数据库：异步数据库会话
    作用：
        1. 查询本地支付记录状态
        2. 返回支付金额、支付状态等信息
    传出：
        包含支付状态、金额、创建时间等信息的字典
    """
    # 调用库函数：构建查询语句
    # 传入：支付记录表模型、筛选条件（内部订单ID == order_id）
    # 作用：构建 SQL 查询对象，筛选出匹配的支付记录
    # 传出：SQLAlchemy Select 查询对象
    查询语句 = select(支付记录表).where(支付记录表.内部订单ID == order_id)

    # 调用库函数：执行异步查询
    # 传入：查询语句
    # 作用：向数据库发送 SELECT 查询，获取结果集
    # 传出：Result 对象，包含所有匹配行
    查询结果 = await 数据库.execute(查询语句)

    # 调用库方法：从结果集中获取所有记录
    # 传入：无
    # 作用：将 Result 对象转换为 Python 列表
    # 传出：list[支付记录表] 类型的列表
    支付记录列表 = 查询结果.scalars().all()

    return {
        "code": 0,
        "data": [
            {
                "id": 记录.id,
                "amount": float(记录.支付金额) if 记录.支付金额 else None,
                "status": 记录.支付状态,
                "paymentMethod": 记录.支付方式,
                "paymentUrl": 记录.支付链接,
                "paidAt": 记录.支付时间.isoformat() if 记录.支付时间 else None,
                "createdAt": 记录.创建时间.isoformat() if 记录.创建时间 else None,
            }
            for 记录 in 支付记录列表
        ],
    }
