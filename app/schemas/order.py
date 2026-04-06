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
        populate_by_name = True


class OrderCreate(BaseModel):
    """创建订单"""
    gameId: int
    accountInfo: str
    requirements: Optional[str] = None
    items: List[OrderItemCreate] = Field(..., min_length=1, description="至少选择一个项目")


class OrderResponse(BaseModel):
    """订单响应"""
    id: int
    orderNo: str = Field(alias="order_no")
    userId: int = Field(alias="user_id")
    userName: Optional[str] = Field(default=None, alias="user_name")
    gameId: int = Field(alias="game_id")
    gameName: Optional[str] = Field(default=None, alias="game_name")
    items: List[OrderItemResponse] = []
    totalAmount: Decimal = Field(alias="total_amount")
    status: str
    handlerId: Optional[int] = Field(default=None, alias="handler_id")
    handlerName: Optional[str] = Field(default=None, alias="handler_name")
    acceptedAt: Optional[datetime] = Field(default=None, alias="accepted_at")
    accountInfo: Optional[str] = Field(default=None, alias="account_info")
    requirements: Optional[str] = None
    attachments: Optional[List[str]] = None
    completionProof: Optional[List[str]] = Field(default=None, alias="completion_proof")
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")
    completedAt: Optional[datetime] = Field(default=None, alias="completed_at")
    cancelledAt: Optional[datetime] = Field(default=None, alias="cancelled_at")
    userRating: Optional[int] = Field(default=None, alias="user_rating")
    userComment: Optional[str] = Field(default=None, alias="user_comment")
    handlerRating: Optional[int] = Field(default=None, alias="handler_rating")
    handlerComment: Optional[str] = Field(default=None, alias="handler_comment")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class OrderPoolItem(BaseModel):
    """订单池项目"""
    id: int
    orderNo: str = Field(alias="order_no")
    gameName: str = Field(alias="game_name")
    itemSummary: str = Field(alias="item_summary", description="项目摘要，如：排位赛代打 x5, 日常任务 x10")
    totalAmount: Decimal = Field(alias="total_amount")
    requirements: Optional[str] = None
    createdAt: datetime = Field(alias="created_at")
    
    class Config:
        from_attributes = True
        populate_by_name = True


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
