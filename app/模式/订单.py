from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class 订单项目创建(BaseModel):
    """创建订单时的项目信息"""
    projectId: int
    quantity: int = Field(..., ge=1, description="数量必须大于等于1")


class 订单项目响应(BaseModel):
    """订单项目的响应数据结构"""
    id: int
    projectId: int
    projectName: str
    quantity: int
    unitPrice: Decimal
    totalPrice: Decimal

    class Config:
        from_attributes = True


class 订单创建(BaseModel):
    """创建订单请求体"""
    gameId: int
    accountInfo: str
    requirements: Optional[str] = None
    items: List[订单项目创建] = Field(..., min_length=1, description="至少选择一个项目")


class 订单响应(BaseModel):
    """订单详情的响应数据结构"""
    id: int
    orderNo: str
    userId: int
    userName: Optional[str] = None
    gameId: int
    gameName: Optional[str] = None
    items: List[订单项目响应] = []
    totalAmount: Decimal
    status: str
    handlerId: Optional[int] = None
    handlerName: Optional[str] = None
    acceptedAt: Optional[datetime] = None
    accountInfo: Optional[str] = None
    requirements: Optional[str] = None
    attachments: Optional[List[str]] = None
    completionProof: Optional[List[str]] = None
    abnormalReason: Optional[str] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    cancelledAt: Optional[datetime] = None
    userRating: Optional[int] = None
    userComment: Optional[str] = None
    handlerRating: Optional[int] = None
    handlerComment: Optional[str] = None

    class Config:
        from_attributes = True


class 订单池项目(BaseModel):
    """订单池中每个项目的摘要信息"""
    id: int
    orderNo: str
    gameName: str
    itemSummary: str
    totalAmount: Decimal
    requirements: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True


class 订单状态更新(BaseModel):
    """更新订单状态的请求体"""
    action: str
    remark: Optional[str] = None
    completionProof: Optional[List[str]] = None


class 订单评价(BaseModel):
    """订单评价请求体"""
    role: str = Field(..., pattern="^(user|handler)$")
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
