from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from app.数据库.会话 import 数据库基类


class 用户表(数据库基类):
    """用户账号表，存储普通用户的注册信息和状态"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    邮箱 = Column("email", String(100), unique=True, index=True, nullable=False, comment="邮箱")
    手机号 = Column("phone", String(20), nullable=True, comment="手机号")
    密码哈希 = Column("password", String(255), nullable=False, comment="Argon2 哈希密码")
    用户名 = Column("username", String(50), unique=True, nullable=False, comment="显示昵称")
    头像链接 = Column("avatar", String(255), nullable=True, comment="用户头像 URL")
    状态 = Column("status", Integer, default=0, comment="状态: 0=正常, 1=封禁")
    余额 = Column("balance", DECIMAL(10, 2), nullable=True, comment="用户余额")
    注册时间 = Column("created_at", DateTime, default=datetime.now, comment="注册时间")
    更新时间 = Column("updated_at", DateTime, nullable=True, comment="更新时间")

    订单列表 = relationship("订单表", back_populates="用户", foreign_keys="订单表.用户ID")


class 打手表(数据库基类):
    """打手（接单者）账号表，存储打手注册信息、等级和审核状态"""

    __tablename__ = "handlers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    邮箱 = Column("email", String(100), unique=True, index=True, nullable=False, comment="邮箱")
    手机号 = Column("phone", String(20), nullable=True, comment="手机号")
    密码哈希 = Column("password", String(255), nullable=False, comment="Argon2 哈希密码")
    用户名 = Column("username", String(50), unique=True, nullable=False, comment="显示昵称")
    头像链接 = Column("avatar", String(255), nullable=True, comment="打手头像 URL")
    状态 = Column("status", Integer, default=0, comment="状态: 0=正常, 1=封禁")
    余额 = Column("balance", DECIMAL(10, 2), nullable=True, comment="打手余额")
    等级 = Column("level", Integer, default=1, comment="打手等级")
    总订单数 = Column("total_orders", Integer, nullable=True, comment="总完成订单数")
    完成率 = Column("completion_rate", DECIMAL(5, 2), nullable=True, comment="订单完成率")
    注册时间 = Column("created_at", DateTime, default=datetime.now, comment="注册时间")
    更新时间 = Column("updated_at", DateTime, nullable=True, comment="更新时间")

    打手订单列表 = relationship("订单表", back_populates="打手", foreign_keys="订单表.打手ID")


class 管理员表(数据库基类):
    """管理员账号表，区分超级管理员和普通管理员"""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    邮箱 = Column("email", String(120), unique=True, index=True, nullable=False, comment="邮箱")
    用户名 = Column("username", String(50), unique=True, nullable=False, comment="管理员用户名")
    密码哈希 = Column("password", String(255), nullable=False, comment="Argon2 哈希密码")
    角色 = Column("role", String(20), default="operator", comment="角色: super=超级管理员, operator=普通管理员")
    状态 = Column("status", Integer, default=0, comment="状态: 0=正常, 1=封禁")
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="创建时间")
    最后登录时间 = Column("last_login_at", DateTime, nullable=True, comment="最后登录时间")

    权限列表 = relationship("管理员权限表", back_populates="管理员", cascade="all, delete-orphan")


class 管理员权限表(数据库基类):
    """管理员权限映射表，记录每个普通管理员可访问的功能"""

    __tablename__ = "admin_permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    管理员ID = Column("admin_id", Integer, ForeignKey("admins.id"), nullable=False, comment="关联的管理员 ID")
    权限键 = Column("permission_key", String(50), nullable=False, comment="权限标识符，例如 view_users, manage_handlers")
    创建时间 = Column("created_at", DateTime, default=datetime.now, comment="创建时间")

    管理员 = relationship("管理员表", back_populates="权限列表")