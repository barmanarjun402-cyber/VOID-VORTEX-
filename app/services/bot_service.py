from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.bot import Bot


class BotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_bot(
        self,
        owner_id: str,
        name: str,
        slug: str,
        source_type: str,
        source_url: str | None,
        deploy_path: str,
        cpu_limit: int,
        ram_limit_mb: int,
    ) -> Bot:
        bot = Bot(
            owner_id=owner_id,
            name=name,
            slug=slug,
            source_type=source_type,
            source_url=source_url,
            deploy_path=deploy_path,
            cpu_limit=cpu_limit,
            ram_limit_mb=ram_limit_mb,
            status="queued",
        )
        self.db.add(bot)
        await self.db.commit()
        await self.db.refresh(bot)
        return bot

    async def list_bots_by_user(self, owner_id: str) -> list[Bot]:
        res = await self.db.execute(select(Bot).where(Bot.owner_id == owner_id).order_by(Bot.created_at.desc()))
        return list(res.scalars().all())

    async def count_bots_by_user(self, owner_id: str) -> int:
        res = await self.db.execute(select(func.count()).select_from(Bot).where(Bot.owner_id == owner_id))
        return int(res.scalar() or 0)

    async def get_bot(self, bot_id: str, owner_id: str | None = None) -> Bot | None:
        stmt = select(Bot).where(Bot.id == bot_id)
        if owner_id:
            stmt = stmt.where(Bot.owner_id == owner_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_status(self, bot: Bot, status: str, container_id: str | None = None) -> Bot:
        bot.status = status
        if container_id:
            bot.container_id = container_id
        await self.db.commit()
        await self.db.refresh(bot)
        return bot
