from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session, get_redis
from app.schemas.bot import DeployGithubRequest, DeployZipResponse
from app.services.bot_service import BotService
from app.services.deployment_service import DeploymentService
from app.services.queue_service import QueueService
from app.services.user_service import UserService
from app.services.validator_service import ValidatorService

router = APIRouter(prefix="/deploy", tags=["deploy"])


@router.post("/github", response_model=DeployZipResponse)
async def deploy_from_github(
    payload: DeployGithubRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
):
    validator = ValidatorService()
    if not validator.validate_github_repo(str(payload.repo_url)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid repo")

    bot_service = BotService(db)
    total = await bot_service.count_bots_by_user(user.id)
    if not await UserService(db).check_bot_limit(user, total):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bot limit reached")

    deployment = DeploymentService()
    safe_name = validator.sanitize_name(payload.name)
    slug, deploy_path = deployment.prepare_source_dir(safe_name)

    bot = await bot_service.create_bot(
        owner_id=user.id,
        name=safe_name,
        slug=slug,
        source_type="github",
        source_url=str(payload.repo_url),
        deploy_path=str(deploy_path),
        cpu_limit=payload.cpu_limit,
        ram_limit_mb=payload.ram_limit_mb,
    )

    await QueueService(redis).enqueue_deploy(
        {
            "bot_id": bot.id,
            "source_type": "github",
            "repo_url": str(payload.repo_url),
            "branch": payload.branch,
            "deploy_path": str(deploy_path),
        }
    )
    return DeployZipResponse(bot_id=bot.id, status="queued")


@router.post("/zip", response_model=DeployZipResponse)
async def deploy_from_zip(
    name: str,
    cpu_limit: int,
    ram_limit_mb: int,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
):
    validator = ValidatorService()
    safe_name = validator.sanitize_name(name)
    deployment = DeploymentService()
    slug, deploy_path = deployment.prepare_source_dir(safe_name)

    archive_path = Path(deploy_path) / "upload.zip"
    async with aiofiles.open(archive_path, "wb") as handle:
        while chunk := await file.read(1024 * 1024):
            await handle.write(chunk)

    try:
        validator.validate_zip(archive_path)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    bot = await BotService(db).create_bot(
        owner_id=user.id,
        name=safe_name,
        slug=slug,
        source_type="zip",
        source_url=None,
        deploy_path=str(deploy_path),
        cpu_limit=cpu_limit,
        ram_limit_mb=ram_limit_mb,
    )

    await QueueService(redis).enqueue_deploy(
        {
            "bot_id": bot.id,
            "source_type": "zip",
            "archive_path": str(archive_path),
            "deploy_path": str(deploy_path),
        }
    )
    return DeployZipResponse(bot_id=bot.id, status="queued")
