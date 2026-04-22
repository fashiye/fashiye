from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models.user import User, Handler, Admin
from app.core.exceptions import AuthError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise AuthError("无效的认证凭据")

    user_id: int = payload.get("sub")
    role: str = payload.get("role")
    
    if user_id is None or role is None:
        raise AuthError("无效的认证凭据")

    if role == "user":
        user = await db.get(User, user_id)
    elif role == "handler":
        user = await db.get(Handler, user_id)
    elif role in ["super", "operator"]:
        # Admin模型的role字段只包含'super'和'operator'两种角色
        # 登录时会将用户选择的'admin'角色替换为数据库中的实际角色
        user = await db.get(Admin, user_id)
    else:
        raise AuthError("无效的角色")

    if not user or user.status != 1:
        raise AuthError("用户不存在或已被禁用")
    
    return user, role


def require_role(allowed_roles: list):
    async def dependency(user_role=Depends(get_current_user)):
        user, role = user_role
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user, role
    return dependency