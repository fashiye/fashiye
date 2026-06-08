from pydantic import BaseModel
from typing import Optional


class 游戏创建(BaseModel):
    """创建游戏的请求体"""
    name: str
    description: str
    icon: Optional[str] = None


class 游戏响应(BaseModel):
    """游戏信息的响应数据结构"""
    id: int
    name: str
    description: str
    icon: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, 模型对象):
        """从 SQLAlchemy 模型转换为 Pydantic 响应"""
        return cls(
            id=模型对象.id,
            name=模型对象.名称,
            description=模型对象.描述 or "",
            icon=模型对象.图标链接,
            created_at=模型对象.创建时间.isoformat() if 模型对象.创建时间 else None
        )


class 项目创建(BaseModel):
    """创建项目的请求体"""
    name: str
    description: str
    price: float
    unit: str
    icon: Optional[str] = None
    is_single_per_order: Optional[bool] = False


class 项目响应(BaseModel):
    """项目信息的响应数据结构"""
    id: int
    gameId: int
    name: str
    description: Optional[str] = None
    price: float
    unit: Optional[str] = None
    icon: Optional[str] = None
    is_single_per_order: Optional[bool] = False
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, 模型对象):
        """从 SQLAlchemy 模型转换为 Pydantic 响应"""
        return cls(
            id=模型对象.id,
            gameId=模型对象.游戏ID,
            name=模型对象.名称,
            description=模型对象.描述,
            price=模型对象.单价_分 / 100,
            unit=模型对象.价格类型,
            icon=None,
            is_single_per_order=False,
            createdAt=模型对象.创建时间.isoformat() if 模型对象.创建时间 else None
        )
