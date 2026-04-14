from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, Request

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimiter
from app.db.base import Base
from app.db.session import engine, redis_client
from app.utils.premium_job import downgrade_expired_premium

settings = get_settings()
configure_logging(settings.log_level)

scheduler = AsyncIOScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    scheduler.add_job(downgrade_expired_premium, "interval", minutes=5)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(v1_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    await RateLimiter(redis_client).guard(request)
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}
