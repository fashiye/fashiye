from pydantic import BaseModel, EmailStr
from typing import Optional
from decimal import Decimal


class 用户注册(BaseModel):
    """用户注册请求体"""
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: str
    verification_code: str


class 发送验证码请求(BaseModel):
    """发送验证码请求体"""
    email: EmailStr
    scene: str = "register"


class 用户登录(BaseModel):
    """用户登录请求体"""
    email: EmailStr
    password: str
    role: str


class 忘记密码请求(BaseModel):
    """忘记密码请求体，发送重置验证码"""
    email: EmailStr
    role: str


class 重置密码请求(BaseModel):
    """重置密码请求体"""
    email: EmailStr
    role: str
    verification_code: str
    new_password: str


class 用户信息响应(BaseModel):
    """用户信息的响应数据结构"""
    id: int
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status: int
    balance: Optional[Decimal] = None
    level: Optional[int] = None
    total_orders: Optional[int] = None
    completion_rate: Optional[Decimal] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True


class 令牌响应(BaseModel):
    """登录成功后返回的 JWT 令牌和用户信息"""
    access_token: str
    token_type: str
    user: 用户信息响应
