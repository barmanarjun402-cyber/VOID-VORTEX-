from pyrogram import Client, filters

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
logger = get_logger(__name__)

controller = Client(
    "void-vortex-controller",
    api_id=settings.telegram_api_id,
    api_hash=settings.telegram_api_hash,
    bot_token=settings.telegram_bot_token,
)


@controller.on_message(filters.command("health"))
async def health_handler(client: Client, message):
    _ = client
    await message.reply_text("VOID VORTEX controller is online")


@controller.on_message(filters.command("stats"))
async def stats_handler(client: Client, message):
    _ = client
    await message.reply_text("Runtime metrics available in dashboard")


def run_controller() -> None:
    configure_logging()
    logger.info("starting_telegram_controller")
    controller.run()


if __name__ == "__main__":
    run_controller()
