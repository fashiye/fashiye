from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.数据库.会话 import 获取数据库会话
from app.模型.游戏 import 游戏表, 项目表

router = APIRouter()


@router.get("/games")
async def 获取游戏列表接口(
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """获取所有已启用的游戏列表（从数据库查询）"""
    # 调用库函数：执行数据库查询
    # 传入：select(游戏表) 查询语句
    # 作用：从 games 表中查询所有状态为启用的游戏
    # 传出：查询结果对象
    查询 = select(游戏表).where(游戏表.状态 == 1).order_by(游戏表.id)
    结果 = await 数据库.execute(查询)
    游戏列表 = 结果.scalars().all()
    return [
        {
            "id": 游戏.id,
            "name": 游戏.名称,
            "description": 游戏.描述 or "",
            "icon": 游戏.图标
        }
        for 游戏 in 游戏列表
    ]


@router.get("/games/{game_id}/projects")
async def 获取游戏项目列表接口(
    game_id: int,
    数据库: AsyncSession = Depends(获取数据库会话)
):
    """获取指定游戏下的所有已启用的项目列表（从数据库查询）"""
    # 调用库函数：执行数据库查询
    # 传入：select(项目表) 过滤条件(game_id匹配且状态为启用)
    # 作用：从 projects 表中查询指定游戏的项目
    # 传出：查询结果对象
    查询 = select(项目表).where(
        项目表.游戏ID == game_id,
        项目表.状态 == 1
    ).order_by(项目表.排序, 项目表.id)
    结果 = await 数据库.execute(查询)
    项目列表 = 结果.scalars().all()
    return [
        {
            "id": 项目.id,
            "gameId": 项目.游戏ID,
            "name": 项目.名称,
            "description": 项目.描述 or "",
            # 调用库函数：价格单位转换
            # 传入：项目.价格（数据库存储单位为分）
            # 作用：将数据库中的"分"转换为用户展示的"元"
            # 传出：浮点数，单位为元
            "price": (项目.价格 or 0) / 100.0,
            "unit": "fixed"
        }
        for 项目 in 项目列表
    ]
