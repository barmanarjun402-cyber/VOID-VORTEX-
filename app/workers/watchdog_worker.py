import asyncio

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.db.models.bot import Bot
from app.db.session import SessionLocal
from app.services.monitoring_service import MonitoringService

logger = get_logger(__name__)


async def run_watchdog() -> None:
    while True:
        async with SessionLocal() as db:
            bots = list((await db.execute(select(Bot).where(Bot.status == "running"))).scalars().all())
            service = MonitoringService(db)
            for bot in bots:
                try:
                    await service.poll_bot(bot)
                except Exception as exc:
                    logger.error("watchdog_poll_failed", bot_id=bot.id, error=str(exc))
        await asyncio.sleep(15)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run_watchdog())
