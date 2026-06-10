from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import timedelta
from decimal import Decimal

from app.数据库.会话 import 获取数据库会话
from app.核心.配置 import 配置对象
from app.核心.安全 import (
    创建访问令牌, 验证密码明文, 生成密码哈希, 解码令牌
)
from app.核心.异常 import 业务逻辑错误
from app.模式.用户 import (
    用户注册, 用户登录, 用户信息响应, 令牌响应,
    忘记密码请求, 重置密码请求, 发送验证码请求
)
from app.模型.用户 import 用户表, 打手表, 管理员表
from app.服务.验证码服务 import 验证码服务对象
from app.工具.限流器 import 登录限流器, 注册限流器, 发送验证码限流器, 限流依赖

router = APIRouter()


@router.post("/auth/register")
async def 注册接口(
    注册数据: 用户注册,
    请求: Request,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    await 限流依赖(注册限流器, 请求)
    """
    用户注册接口

    支持三种角色: user（普通用户）、handler（打手）、admin（管理员）
    注册时需要提供邮箱验证码
    """
    if not await 验证码服务对象.异步校验验证码(注册数据.email, "register", 注册数据.verification_code):
        raise 业务逻辑错误("验证码错误或已过期")

    if 注册数据.role == "user":
        用户结果 = await 数据库.execute(select(用户表).where(用户表.邮箱 == 注册数据.email))
        if 用户结果.scalar_one_or_none():
            raise 业务逻辑错误("该邮箱已被注册")
        新用户 = 用户表(
            用户名=注册数据.username,
            邮箱=注册数据.email,
            手机号=注册数据.phone,
            密码哈希=生成密码哈希(注册数据.password),
        )
    elif 注册数据.role == "handler":
        打手结果 = await 数据库.execute(select(打手表).where(打手表.邮箱 == 注册数据.email))
        if 打手结果.scalar_one_or_none():
            raise 业务逻辑错误("该邮箱已被注册")
        新用户 = 打手表(
            用户名=注册数据.username,
            邮箱=注册数据.email,
            手机号=注册数据.phone,
            密码哈希=生成密码哈希(注册数据.password),
        )
    elif 注册数据.role == "admin":
        管理员结果 = await 数据库.execute(select(管理员表).where(管理员表.邮箱 == 注册数据.email))
        if 管理员结果.scalar_one_or_none():
            raise 业务逻辑错误("该邮箱已被注册")
        新用户 = 管理员表(
            用户名=注册数据.username,
            邮箱=注册数据.email,
            密码哈希=生成密码哈希(注册数据.password),
            角色="operator"
        )
    else:
        raise 业务逻辑错误("无效的角色类型")

    数据库.add(新用户)
    await 数据库.commit()
    return {"code": 0, "data": {"userId": 新用户.id}, "message": "注册成功"}


@router.post("/auth/login", response_model=令牌响应)
async def 登录接口(
    登录数据: 用户登录,
    请求: Request,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    await 限流依赖(登录限流器, 请求)
    """
    用户登录接口

    支持 user、handler、admin 三种角色登录
    登录成功后返回 JWT 访问令牌和用户信息
    """
    用户模型 = 用户表
    if 登录数据.role == "handler":
        用户模型 = 打手表
    elif 登录数据.role == "admin":
        用户模型 = 管理员表
    elif 登录数据.role != "user":
        raise 业务逻辑错误("无效的角色类型")

    查询 = select(用户模型).where(用户模型.邮箱 == 登录数据.email)
    结果 = await 数据库.execute(查询)
    用户 = 结果.scalar_one_or_none()

    if not 用户 or not 验证密码明文(登录数据.password, 用户.密码哈希):
        raise 业务逻辑错误("邮箱或密码错误")

    if 用户.状态 != 0:
        raise 业务逻辑错误("账户已被禁用")

    实际角色 = 登录数据.role
    if 登录数据.role == "admin" and hasattr(用户, '角色'):
        实际角色 = 用户.角色

    访问令牌过期时间 = timedelta(minutes=配置对象.访问令牌过期分钟数)
    访问令牌 = 创建访问令牌(
        # 传入：用户ID（转字符串）和实际角色
        # 作用：生成 JWT 访问令牌，python-jose 要求 sub 为字符串类型
        # 传出：JWT 令牌字符串
        待编码数据={"sub": str(用户.id), "role": 实际角色},
        过期时间差=访问令牌过期时间
    )

    return {
        "access_token": 访问令牌,
        "token_type": "bearer",
        "user": 用户信息响应(
            id=用户.id,
            username=用户.用户名,
            email=用户.邮箱,
            phone=getattr(用户, '手机号', None),
            avatar=getattr(用户, '头像链接', None),
            status=用户.状态,
            role=实际角色
        )
    }


@router.post("/auth/send-code")
async def 发送验证码接口(
    请求数据: 发送验证码请求,
    请求: Request,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    await 限流依赖(发送验证码限流器, 请求)
    """
    发送邮箱注册验证码

    验证码有效期15分钟，发送前检查邮箱是否已被注册
    """
    邮箱 = 请求数据.email
    场景 = 请求数据.scene

    if not 邮箱:
        raise 业务逻辑错误("请提供邮箱地址")

    if 场景 == "register":
        用户结果 = await 数据库.execute(select(用户表).where(用户表.邮箱 == 邮箱))
        if 用户结果.scalar_one_or_none():
            raise 业务逻辑错误("该邮箱已被注册")
        打手结果 = await 数据库.execute(select(打手表).where(打手表.邮箱 == 邮箱))
        if 打手结果.scalar_one_or_none():
            raise 业务逻辑错误("该邮箱已被注册")

    await 验证码服务对象.发送并缓存验证码(邮箱, 场景)
    return {"code": 0, "data": None, "message": "验证码已发送"}


@router.post("/auth/forgot-password")
async def 忘记密码接口(
    请求数据: 忘记密码请求,
    请求: Request,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    await 限流依赖(发送验证码限流器, 请求)
    """
    忘记密码 - 发送密码重置验证码

    验证码有效期10分钟
    """
    邮箱 = 请求数据.email
    角色 = 请求数据.role

    用户模型 = 用户表
    if 角色 == "handler":
        用户模型 = 打手表
    elif 角色 == "admin":
        用户模型 = 管理员表

    结果 = await 数据库.execute(select(用户模型).where(用户模型.邮箱 == 邮箱))
    用户 = 结果.scalar_one_or_none()
    if not 用户:
        raise 业务逻辑错误("该邮箱未注册")

    await 验证码服务对象.发送并缓存重置密码验证码(邮箱)
    return {"code": 0, "data": None, "message": "重置密码验证码已发送"}


@router.post("/auth/reset-password")
async def 重置密码接口(
    请求数据: 重置密码请求,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """
    重置密码 - 使用验证码设置新密码

    验证码校验通过后直接将密码更新为新密码
    """
    if not await 验证码服务对象.异步校验验证码(请求数据.email, "reset_password", 请求数据.verification_code):
        raise 业务逻辑错误("验证码错误或已过期")

    用户模型 = 用户表
    if 请求数据.role == "handler":
        用户模型 = 打手表
    elif 请求数据.role == "admin":
        用户模型 = 管理员表

    结果 = await 数据库.execute(select(用户模型).where(用户模型.邮箱 == 请求数据.email))
    用户 = 结果.scalar_one_or_none()
    if not 用户:
        raise 业务逻辑错误("用户不存在")

    用户.密码哈希 = 生成密码哈希(请求数据.new_password)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "密码重置成功"}
