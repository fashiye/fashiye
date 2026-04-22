from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.user import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.models.user import User, Handler, Admin
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.exceptions import BusinessError
from app.services.email_service import email_service
from app.services.verification_service import verification_service
from pydantic import BaseModel
import re

router = APIRouter(prefix="/auth", tags=["auth"])


class SendCodeRequest(BaseModel):
    email: str


PASSWORD_MIN_LENGTH = 6


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"密码长度至少{PASSWORD_MIN_LENGTH}位"
    if not re.search(r'[a-zA-Z]', password):
        return False, "密码必须包含字母"
    if not re.search(r'\d', password):
        return False, "密码必须包含数字"
    return True, ""


@router.post("/send-code")
async def send_verification_code(req: SendCodeRequest):
    """
    发送注册验证码
    """
    code = verification_service.generate_code()
    
    # 存储验证码
    stored = await verification_service.store_code(req.email, code)
    if not stored:
        raise BusinessError("验证码存储失败")
    
    # 发送邮件
    sent = await email_service.send_verification_code(req.email, code)
    if not sent:
        raise BusinessError("邮件发送失败，请检查邮箱地址")
    
    return {"message": "验证码已发送"}


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 验证验证码
    is_valid = await verification_service.verify_code(user_data.email, user_data.verification_code)
    if not is_valid:
        raise BusinessError("验证码错误或已过期")
    
    if user_data.role == "user":
        result = await db.execute(
            select(User).where((User.username == user_data.username) | (User.email == user_data.email))
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise BusinessError("用户名或邮箱已存在")
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            password=get_password_hash(user_data.password),
            phone=user_data.phone
        )
        db.add(user)
    elif user_data.role == "handler":
        result = await db.execute(
            select(Handler).where((Handler.username == user_data.username) | (Handler.email == user_data.email))
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise BusinessError("用户名或邮箱已存在")
        
        user = Handler(
            username=user_data.username,
            email=user_data.email,
            password=get_password_hash(user_data.password),
            phone=user_data.phone
        )
        db.add(user)
    elif user_data.role == "admin":
        result = await db.execute(
            select(Admin).where((Admin.username == user_data.username) | (Admin.email == user_data.email))
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise BusinessError("用户名或邮箱已存在")
        
        user = Admin(
            username=user_data.username,
            email=user_data.email,
            password=get_password_hash(user_data.password)
        )
        db.add(user)
    else:
        raise BusinessError("无效的角色")
    
    await db.commit()
    await db.refresh(user)
    
    token = create_access_token({"sub": str(user.id), "role": user_data.role})
    
    user_data_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "status": user.status,
        "role": user_data.role
    }
    
    if hasattr(user, 'phone'):
        user_data_dict["phone"] = user.phone
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user_data_dict)
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    role = user_data.role
    model_map = {
        "user": User,
        "handler": Handler,
        "admin": Admin
    }
    
    model = model_map.get(role)
    if not model:
        raise HTTPException(status_code=400, detail="无效的角色")
    
    result = await db.execute(select(model).where(model.username == user_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if user.status != 1:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    
    # 确定实际角色：对于Admin使用数据库中的角色，其他使用输入角色
    actual_role = role
    if isinstance(user, Admin):
        actual_role = user.role
    
    token = create_access_token({"sub": str(user.id), "role": actual_role})
    
    user_response_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "status": user.status,
        "role": actual_role
    }
    
    if hasattr(user, 'phone'):
        user_response_data["phone"] = user.phone
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(**user_response_data)
    )


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    发送密码重置验证码
    """
    rate_allowed = await verification_service.check_rate_limit(
        f"forgot:{req.email}", 
        max_requests=3, 
        window_seconds=300
    )
    if not rate_allowed:
        remaining = await verification_service.get_rate_limit_remaining(f"forgot:{req.email}")
        raise BusinessError(f"请求过于频繁，请{remaining}秒后再试")
    
    role = req.role
    model_map = {
        "user": User,
        "handler": Handler,
        "admin": Admin
    }
    
    model = model_map.get(role)
    if not model:
        raise BusinessError("无效的角色")
    
    result = await db.execute(select(model).where(model.email == req.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise BusinessError("该邮箱未注册")
    
    if user.status != 1:
        raise BusinessError("账号已被禁用，请联系管理员")
    
    code = verification_service.generate_code()
    
    stored = await verification_service.store_reset_code(req.email, code)
    if not stored:
        raise BusinessError("验证码存储失败")
    
    sent = await email_service.send_password_reset_code(req.email, code)
    if not sent:
        raise BusinessError("邮件发送失败，请检查邮箱地址")
    
    return {"message": "密码重置验证码已发送"}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    重置密码
    """
    rate_allowed = await verification_service.check_rate_limit(
        f"reset:{req.email}", 
        max_requests=5, 
        window_seconds=300
    )
    if not rate_allowed:
        remaining = await verification_service.get_rate_limit_remaining(f"reset:{req.email}")
        raise BusinessError(f"请求过于频繁，请{remaining}秒后再试")
    
    is_valid = await verification_service.verify_reset_code(req.email, req.verification_code)
    if not is_valid:
        raise BusinessError("验证码错误或已过期")
    
    is_strong, msg = validate_password_strength(req.new_password)
    if not is_strong:
        raise BusinessError(msg)
    
    role = req.role
    model_map = {
        "user": User,
        "handler": Handler,
        "admin": Admin
    }
    
    model = model_map.get(role)
    if not model:
        raise BusinessError("无效的角色")
    
    result = await db.execute(select(model).where(model.email == req.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise BusinessError("用户不存在")
    
    if user.status != 1:
        raise BusinessError("账号已被禁用，请联系管理员")
    
    user.password = get_password_hash(req.new_password)
    await db.commit()
    
    return {"message": "密码重置成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(user_role=Depends(get_current_user)):
    user, role = user_role
    
    response_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "status": user.status,
        "role": role
    }
    
    if role == "user":
        response_data["balance"] = user.balance
    elif role == "handler":
        response_data["balance"] = user.balance
        response_data["level"] = user.level
        response_data["total_orders"] = user.total_orders
        response_data["completion_rate"] = user.completion_rate
    
    return UserResponse(**response_data)
