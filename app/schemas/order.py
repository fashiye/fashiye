from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class OrderItemCreate(BaseModel):
    """订单项目创建"""
    projectId: int
    quantity: int = Field(..., ge=1, description="数量必须大于等于1")


class OrderItemResponse(BaseModel):
    """订单项目响应"""
    id: int
    projectId: int
    projectName: str
    quantity: int
    unitPrice: Decimal
    totalPrice: Decimal
    
    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """创建订单"""
    gameId: int
    accountInfo: str
    requirements: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1, description="至少选择一个项目")


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    orderNo: str
    userId: int
    userName: Optional[str] = None
    gameId: int
    gameName: Optional[str] = None
    items: List[OrderItemResponse] = []
    totalAmount: Decimal
    status: str
    handlerId: Optional[int] = None
    handlerName: Optional[str] = None
    acceptedAt: Optional[datetime] = None
    accountInfo: Optional[str] = None
    requirements: Optional[str] = None
    attachments: Optional[List[str]] = None
    completionProof: Optional[List[str]] = None
    createdAt: datetime
    updatedAt: datetime
    completedAt: Optional[datetime] = None
    cancelledAt: Optional[datetime] = None
    userRating: Optional[int] = None
    userComment: Optional[str] = None
    handlerRating: Optional[int] = None
    handlerComment: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrderPoolItem(BaseModel):
    """订单池项目"""
    id: int
    orderNo: str
    gameName: str
    itemSummary: str
    totalAmount: Decimal
    requirements: Optional[str] = None
    createdAt: datetime
    
    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    """订单状态更新"""
    action: str
    remark: Optional[str] = None
    completionProof: Optional[List[str]] = None


class OrderRate(BaseModel):
    """订单评价"""
    role: str = Field(..., pattern="^(user|handler)$")
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
