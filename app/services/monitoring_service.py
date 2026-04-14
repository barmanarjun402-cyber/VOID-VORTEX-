from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.bot import Bot
from app.services.container_service import ContainerService

logger = get_logger(__name__)


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.container_service = ContainerService()

    async def poll_bot(self, bot: Bot) -> dict:
        if not bot.container_id:
            return {"status": "no_container"}
        stats = self.container_service.container_stats(bot.container_id)
        mem_usage = stats.get("memory_stats", {}).get("usage", 0)
        cpu_total = stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
        limit_bytes = bot.ram_limit_mb * 1024 * 1024
        if mem_usage > limit_bytes:
            logger.warning("memory_limit_exceeded", bot_id=bot.id, usage=mem_usage, limit=limit_bytes)
            self.container_service.stop_container(bot.container_id)
            bot.status = "killed_abuse"
            await self.db.commit()
        return {"cpu_total": cpu_total, "memory_usage": mem_usage, "status": bot.status}
