from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.services.bot_service import BotService
from app.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/{bot_id}")
async def get_logs(
    bot_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
):
    bot = await BotService(db).get_bot(bot_id, user.id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    rows = await LogService(db).get_logs(bot_id, limit)
    return [{"level": r.level, "message": r.message, "created_at": r.created_at.isoformat()} for r in rows]
