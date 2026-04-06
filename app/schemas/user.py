from pydantic import BaseModel, EmailStr
from typing import Optional
from decimal import Decimal


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    role: str
    verification_code: str


class UserLogin(BaseModel):
    username: str
    password: str
    role: str


class UserResponse(BaseModel):
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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
