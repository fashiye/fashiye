from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.数据库.会话 import 获取数据库会话
from app.模型.游戏 import 游戏表, 项目表
from app.api.依赖.认证 import 要求角色
from app.核心.异常 import 业务逻辑错误

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


# ─── P1-3: 游戏 CRUD ───────────────────────────────────────────────


@router.post("/games")
async def 创建游戏接口(
    游戏数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员创建新游戏。
    传入：游戏数据含 name, description（可选）, icon（可选）
    作用：在 games 表中插入新记录
    传出：创建的游戏对象
    """
    新游戏 = 游戏表(
        名称=游戏数据.get("name"),
        描述=游戏数据.get("description", ""),
        图标=游戏数据.get("icon", ""),
        状态=1
    )
    数据库.add(新游戏)
    await 数据库.commit()
    await 数据库.refresh(新游戏)
    return {
        "code": 0,
        "data": {"id": 新游戏.id, "name": 新游戏.名称},
        "message": "游戏创建成功"
    }


@router.put("/games/{game_id}")
async def 更新游戏接口(
    game_id: int,
    游戏数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员更新游戏信息。
    传入：game_id（路径参数，游戏ID），游戏数据含 name, description（可选）, icon（可选）
    作用：更新 games 表中指定记录
    传出：无数据
    """
    游戏结果 = await 数据库.execute(select(游戏表).where(游戏表.id == game_id))
    游戏 = 游戏结果.scalar_one_or_none()
    if not 游戏:
        raise 业务逻辑错误("游戏不存在")
    if "name" in 游戏数据:
        游戏.名称 = 游戏数据["name"]
    if "description" in 游戏数据:
        游戏.描述 = 游戏数据["description"]
    if "icon" in 游戏数据:
        游戏.图标 = 游戏数据["icon"]
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "游戏更新成功"}


@router.delete("/games/{game_id}")
async def 删除游戏接口(
    game_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员删除游戏及其所有项目。
    传入：game_id（路径参数，游戏ID）
    作用：级联删除游戏及关联项目
    传出：无数据
    """
    游戏结果 = await 数据库.execute(select(游戏表).where(游戏表.id == game_id))
    游戏 = 游戏结果.scalar_one_or_none()
    if not 游戏:
        raise 业务逻辑错误("游戏不存在")
    await 数据库.delete(游戏)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "游戏已删除"}


@router.post("/games/{game_id}/projects")
async def 创建项目接口(
    game_id: int,
    项目数据: dict,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员在指定游戏下创建项目。
    传入：game_id（路径参数，游戏ID），项目数据含 name, description, price, unit, icon, is_single_per_order
    作用：在 projects 表中插入新记录，价格从元转换为分存储
    传出：创建的项目对象
    """
    游戏结果 = await 数据库.execute(select(游戏表).where(游戏表.id == game_id))
    游戏 = 游戏结果.scalar_one_or_none()
    if not 游戏:
        raise 业务逻辑错误("游戏不存在")
    新项目 = 项目表(
        游戏ID=game_id,
        名称=项目数据.get("name"),
        描述=项目数据.get("description", ""),
        价格=int((项目数据.get("price") or 0) * 100),  # 元转分
        价格类型="fixed",  # 默认一口价计价
        单位名称=项目数据.get("unit", "次"),
        图标=项目数据.get("icon", ""),
        每单限购=1 if 项目数据.get("is_single_per_order") else 0,
        状态=1
    )
    数据库.add(新项目)
    await 数据库.commit()
    await 数据库.refresh(新项目)
    return {
        "code": 0,
        "data": {"id": 新项目.id, "name": 新项目.名称},
        "message": "项目创建成功"
    }


@router.delete("/games/{game_id}/projects/{project_id}")
async def 删除项目接口(
    game_id: int,
    project_id: int,
    数据库: AsyncSession = Depends(获取数据库会话),
    当前用户信息: tuple = Depends(要求角色(["super", "operator"]))
):
    """
    管理员删除指定项目。
    传入：game_id（路径参数，游戏ID），project_id（路径参数，项目ID）
    作用：从 projects 表中删除指定记录
    传出：无数据
    """
    项目结果 = await 数据库.execute(
        select(项目表).where(项目表.id == project_id, 项目表.游戏ID == game_id)
    )
    项目 = 项目结果.scalar_one_or_none()
    if not 项目:
        raise 业务逻辑错误("项目不存在")
    await 数据库.delete(项目)
    await 数据库.commit()
    return {"code": 0, "data": None, "message": "项目已删除"}
