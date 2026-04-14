from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.bot import BotResponse
from app.services.bot_service import BotService
from app.services.container_service import ContainerService

router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("", response_model=list[BotResponse])
async def list_bots(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db_session)]):
    bots = await BotService(db).list_bots_by_user(user.id)
    return [
        BotResponse(
            id=b.id,
            name=b.name,
            slug=b.slug,
            status=b.status,
            cpu_limit=b.cpu_limit,
            ram_limit_mb=b.ram_limit_mb,
            uptime_seconds=b.uptime_seconds,
        )
        for b in bots
    ]


@router.post("/{bot_id}/start")
async def start_bot(bot_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    service = BotService(db)
    bot = await service.get_bot(bot_id, user.id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if not bot.container_id:
        raise HTTPException(status_code=400, detail="Bot not deployed")
    ContainerService().restart_container(bot.container_id)
    await service.update_status(bot, "running")
    return {"status": "running"}


@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    service = BotService(db)
    bot = await service.get_bot(bot_id, user.id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if not bot.container_id:
        raise HTTPException(status_code=400, detail="Bot not deployed")
    ContainerService().stop_container(bot.container_id)
    await service.update_status(bot, "stopped")
    return {"status": "stopped"}


@router.post("/{bot_id}/restart")
async def restart_bot(bot_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    service = BotService(db)
    bot = await service.get_bot(bot_id, user.id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if not bot.container_id:
        raise HTTPException(status_code=400, detail="Bot not deployed")
    ContainerService().restart_container(bot.container_id)
    bot.restart_count += 1
    await service.update_status(bot, "running")
    return {"status": "running", "restart_count": bot.restart_count}
