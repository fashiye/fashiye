from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.核心.配置 import 配置对象

引擎参数 = {
    "echo": 配置对象.调试模式,
    "future": True,
}

if "mysql" in 配置对象.数据库连接字符串.lower():
    引擎参数.update({
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "pool_timeout": 30,
    })

引擎 = create_async_engine(配置对象.数据库连接字符串, **引擎参数)

异步会话工厂 = sessionmaker(
    引擎, class_=AsyncSession, expire_on_commit=False
)

数据库基类 = declarative_base()


async def 获取数据库会话():
    """获取异步数据库会话的生成器函数，用于 FastAPI 依赖注入"""
    async with 异步会话工厂() as 会话:
        yield 会话
