from fastapi import HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.limit = get_settings().rate_limit_per_minute

    async def guard(self, request: Request, key_prefix: str = "rate") -> None:
        client_ip = request.client.host if request.client else "anonymous"
        key = f"{key_prefix}:{client_ip}"
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 60)
            if count > self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests",
                )
        except RedisError:
            return
