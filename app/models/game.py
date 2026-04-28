from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text)
    icon = Column(String(255))
    status = Column(SmallInteger, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    projects = relationship("Project", back_populates="game")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    name = Column(String(100))
    description = Column(Text)
    price_type = Column(Enum('fixed', 'unit'), default='fixed')
    price = Column(Integer)
    unit_name = Column(String(20))
    max_quantity = Column(Integer)
    is_single_per_order = Column(SmallInteger, default=0, comment="每单限购一个")
    sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    icon = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    game = relationship("Game", back_populates="projects")
