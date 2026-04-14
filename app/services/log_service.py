from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bot_log import BotLog


class LogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_log(self, bot_id: str, message: str, level: str = "info") -> BotLog:
        row = BotLog(bot_id=bot_id, message=message, level=level)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_logs(self, bot_id: str, limit: int = 100) -> list[BotLog]:
        res = await self.db.execute(
            select(BotLog).where(BotLog.bot_id == bot_id).order_by(BotLog.created_at.desc()).limit(limit)
        )
        return list(res.scalars().all())
