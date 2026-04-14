import asyncio
from pathlib import Path

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.db.models.bot import Bot
from app.db.session import SessionLocal, redis_client
from app.services.bot_service import BotService
from app.services.container_service import ContainerService
from app.services.deployment_service import DeploymentService
from app.services.log_service import LogService
from app.services.queue_service import QueueService
from app.services.validator_service import ValidatorService

logger = get_logger(__name__)


async def process_payload(payload: dict) -> None:
    async with SessionLocal() as db:
        bot = await db.scalar(select(Bot).where(Bot.id == payload["bot_id"]))
        if not bot:
            return

        deploy_service = DeploymentService()
        bot_service = BotService(db)
        log_service = LogService(db)
        validator = ValidatorService()

        source_path = Path(payload["deploy_path"])
        try:
            if payload["source_type"] == "github":
                deploy_service.clone_repo(payload["repo_url"], payload.get("branch", "main"), source_path)
            elif payload["source_type"] == "zip":
                deploy_service.extract_zip(Path(payload["archive_path"]), source_path)

            findings = validator.scan_token_leaks(source_path)
            if findings:
                await bot_service.update_status(bot, "failed")
                await log_service.add_log(bot.id, f"Token leaks detected: {findings}", "error")
                return

            language = deploy_service.detect_language(source_path)
            run_command = deploy_service.detect_run_command(source_path, language)

            container_id = ContainerService().start_bot_container(
                bot.slug, source_path, run_command, bot.cpu_limit, bot.ram_limit_mb
            )
            await bot_service.update_status(bot, "running", container_id=container_id)
            await log_service.add_log(bot.id, f"Deployment successful; container {container_id}")
        except Exception as exc:
            await bot_service.update_status(bot, "failed")
            await log_service.add_log(bot.id, f"Deployment failed: {exc}", "error")
            await QueueService(redis_client).mark_failed(payload, str(exc))


async def run_worker() -> None:
    queue = QueueService(redis_client)
    logger.info("deploy_worker_started")
    while True:
        payload = await queue.dequeue_deploy(timeout=5)
        if payload:
            await process_payload(payload)
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run_worker())
