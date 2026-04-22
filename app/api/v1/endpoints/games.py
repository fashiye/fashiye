from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.permissions import require_role
from app.schemas.game import GameCreate, GameResponse, ProjectCreate, ProjectResponse
from app.models.game import Game, Project
from typing import List

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=GameResponse)
async def create_game(
    game_data: GameCreate,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role(["super", "operator"]))
):
    admin, _ = user_role
    
    game = Game(
        name=game_data.name,
        description=game_data.description,
        icon=game_data.icon
    )
    
    db.add(game)
    await db.commit()
    await db.refresh(game)
    
    return GameResponse.from_orm(game)


@router.get("", response_model=List[GameResponse])
async def get_games(
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, _ = user_role
    
    result = await db.execute(select(Game))
    games = result.scalars().all()
    
    return [GameResponse.from_orm(game) for game in games]


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    game = await db.get(Game, game_id)
    
    if not game:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    return GameResponse.from_orm(game)


@router.post("/{game_id}/projects", response_model=ProjectResponse)
async def create_project(
    game_id: int,
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(require_role(["super", "operator"]))
):
    admin, _ = user_role
    
    game = await db.get(Game, game_id)
    if not game:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    project = Project(
        game_id=game_id,
        name=project_data.name,
        description=project_data.description,
        price=project_data.price,
        unit_name=project_data.unit,
        icon=project_data.icon
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse.from_orm(project)


@router.get("/{game_id}/projects", response_model=List[ProjectResponse])
async def get_projects(
    game_id: int,
    db: AsyncSession = Depends(get_db),
    user_role=Depends(get_current_user)
):
    user, _ = user_role
    
    game = await db.get(Game, game_id)
    if not game:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    result = await db.execute(
        select(Project).where(Project.game_id == game_id)
    )
    projects = result.scalars().all()
    
    return [ProjectResponse.from_orm(project) for project in projects]
