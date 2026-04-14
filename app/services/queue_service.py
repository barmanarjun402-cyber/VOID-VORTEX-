import json

from redis.asyncio import Redis

DEPLOY_QUEUE = "queue:deployments"
FAILURE_QUEUE = "queue:deployments:failed"


class QueueService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def enqueue_deploy(self, payload: dict) -> None:
        await self.redis.lpush(DEPLOY_QUEUE, json.dumps(payload))

    async def dequeue_deploy(self, timeout: int = 5) -> dict | None:
        item = await self.redis.brpop(DEPLOY_QUEUE, timeout=timeout)
        if not item:
            return None
        _, data = item
        return json.loads(data)

    async def mark_failed(self, payload: dict, reason: str) -> None:
        await self.redis.lpush(FAILURE_QUEUE, json.dumps({"payload": payload, "reason": reason}))
