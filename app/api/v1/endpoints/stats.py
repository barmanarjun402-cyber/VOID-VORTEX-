from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.bot import Bot
from app.db.models.user import User
from app.db.session import get_db_session

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def my_stats(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db_session)]):
    total_bots = await db.scalar(select(func.count()).select_from(Bot).where(Bot.owner_id == user.id))
    running_bots = await db.scalar(
        select(func.count()).select_from(Bot).where(Bot.owner_id == user.id, Bot.status == "running")
    )
    return {
        "tier": user.tier,
        "total_bots": int(total_bots or 0),
        "running_bots": int(running_bots or 0),
    }
