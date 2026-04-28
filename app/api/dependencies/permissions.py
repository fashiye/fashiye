from fastapi import Depends, HTTPException
from app.api.dependencies.auth import get_current_user


def require_role(allowed_roles: list):
    async def dependency(user_role=Depends(get_current_user)):
        user, role = user_role
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user, role
    return dependency
