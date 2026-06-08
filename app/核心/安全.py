from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.核心.配置 import 配置对象

密码上下文 = CryptContext(schemes=["argon2"], deprecated="auto")


def 创建访问令牌(待编码数据: dict, 过期时间差: timedelta = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        待编码数据: 需要编码到令牌中的数据字典
        过期时间差: 令牌过期时间差，默认使用配置的过期分钟数

    Returns:
        编码后的 JWT 令牌字符串
    """
    要编码的数据 = 待编码数据.copy()
    过期时间 = datetime.utcnow() + (过期时间差 or timedelta(minutes=配置对象.访问令牌过期分钟数))
    要编码的数据.update({"exp": 过期时间})
    return jwt.encode(要编码的数据, 配置对象.密钥, algorithm=配置对象.加密算法)


def 验证密码明文(明文密码: str, 哈希密码: str) -> bool:
    """
    验证明文密码是否与存储的哈希密码匹配

    Args:
        明文密码: 用户输入的明文密码
        哈希密码: 数据库中存储的哈希密码

    Returns:
        匹配返回 True，否则返回 False
    """
    return 密码上下文.verify(明文密码, 哈希密码)


def 生成密码哈希(密码原文: str) -> str:
    """
    使用 Argon2 算法对密码进行哈希处理

    Args:
        密码原文: 要哈希的明文密码

    Returns:
        哈希后的密码字符串
    """
    return 密码上下文.hash(密码原文)


def 解码令牌(令牌字符串: str) -> dict:
    """
    解码 JWT 令牌并返回载荷数据

    Args:
        令牌字符串: JWT 令牌字符串

    Returns:
        解码后的载荷字典；若令牌无效则返回 None
    """
    try:
        载荷 = jwt.decode(令牌字符串, 配置对象.密钥, algorithms=[配置对象.加密算法])
        return 载荷
    except JWTError:
        return None
