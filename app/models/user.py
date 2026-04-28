from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, SmallInteger, Enum, Text
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(255), nullable=False)
    avatar = Column(String(255))
    status = Column(SmallInteger, default=1)
    balance = Column(DECIMAL(10, 2), default=0.00)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Handler(Base):
    __tablename__ = "handlers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    password = Column(String(255), nullable=False)
    avatar = Column(String(255))
    status = Column(SmallInteger, default=1)
    balance = Column(DECIMAL(10, 2), default=0.00)
    level = Column(SmallInteger, default=1)
    total_orders = Column(Integer, default=0)
    completion_rate = Column(DECIMAL(5, 2), default=100.00)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    avatar = Column(String(255))
    role = Column(Enum('super', 'operator'), default='operator')
    status = Column(SmallInteger, default=1)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
