from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.数据库.会话 import 获取数据库会话
from app.核心.配置 import 配置对象
from app.核心.安全 import 解码令牌
from app.模型.用户 import 用户表, 打手表, 管理员表
from app.核心.异常 import 认证错误

安全方案 = HTTPBearer()


async def 获取当前用户(
    凭据: HTTPAuthorizationCredentials = Depends(安全方案),
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """
    解析请求头中的 JWT 令牌并返回当前用户对象和角色

    支持的角色: user（用户）、handler（打手）、super/operator（管理员）

    Args:
        凭据: HTTP Authorization header 中的 Bearer 令牌
        数据库: 异步数据库会话

    Returns:
        (user, role) 元组，user 为对应的 ORM 模型实例

    Raises:
        认证错误: 令牌无效、用户不存在或被禁用时抛出
    """
    令牌 = 凭据.credentials
    载荷 = 解码令牌(令牌)

    if not 载荷:
        raise 认证错误("无效的认证凭据")

    # 传入：JWT 载荷字典
    # 作用：提取 sub（用户ID，python-jose 要求 sub 为字符串，须转 int）和 role
    # 传出：用户ID（int）和角色（str）
    用户ID: int = int(载荷.get("sub"))
    角色: str = 载荷.get("role")

    if 用户ID is None or 角色 is None:
        raise 认证错误("无效的认证凭据")

    if 角色 == "user":
        用户 = await 数据库.get(用户表, 用户ID)
    elif 角色 == "handler":
        用户 = await 数据库.get(打手表, 用户ID)
    elif 角色 in ["super", "operator"]:
        # Admin模型的role字段只包含'super'和'operator'两种角色
        # 登录时会将用户选择的'admin'角色替换为数据库中的实际角色
        用户 = await 数据库.get(管理员表, 用户ID)
    else:
        raise 认证错误("无效的角色")

    if not 用户 or 用户.状态 != 0:
        raise 认证错误("用户不存在或已被禁用")

    return 用户, 角色


def 要求角色(允许的角色列表: list):
    """
    创建依赖注入函数，校验当前用户的角色是否在允许列表中

    Args:
        允许的角色列表: 允许通过的角色列表，如 ["super", "operator"]

    Returns:
        依赖注入函数，返回 (user, role) 元组或抛出 403 异常
    """
    async def 角色校验(用户角色=Depends(获取当前用户)):
        用户, 角色 = 用户角色
        if 角色 not in 允许的角色列表:
            raise HTTPException(status_code=403, detail="权限不足")
        return 用户, 角色
    return 角色校验


async def 获取当前用户可选(
    凭据: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """
    可选择获取当前用户信息，无令牌时返回 None（不报错）

    传入：HTTP Authorization header（可选）
    作用：尝试解析 JWT 令牌，令牌无效或缺失时返回 None 而非报错
    传出：(user, role) 元组或 None
    """
    if not 凭据:
        return None
    try:
        return await 获取当前用户(凭据, 数据库)
    except 认证错误:
        return None
