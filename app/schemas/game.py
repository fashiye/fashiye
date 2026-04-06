from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GameCreate(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None


class GameResponse(BaseModel):
    id: int
    name: str
    description: str
    icon: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "name": obj.name,
            "description": obj.description or "",
            "icon": obj.icon,
            "created_at": obj.created_at.isoformat() if obj.created_at else None
        }
        return cls(**data)


class ProjectCreate(BaseModel):
    name: str
    description: str
    price: float
    unit: str
    icon: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    gameId: int
    name: str
    description: Optional[str] = None
    price: float
    unit: Optional[str] = None
    icon: Optional[str] = None
    createdAt: Optional[str] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "gameId": obj.game_id,
            "name": obj.name,
            "description": obj.description,
            "price": obj.price,
            "unit": obj.unit_name,
            "icon": obj.icon,
            "createdAt": obj.created_at.isoformat() if obj.created_at else None
        }
        return cls(**data)
