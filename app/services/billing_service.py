from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.billing import BillingEvent


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(
        self,
        user_id: str,
        provider: str,
        event_type: str,
        external_id: str,
        status: str,
    ) -> BillingEvent:
        row = BillingEvent(
            user_id=user_id,
            provider=provider,
            event_type=event_type,
            external_id=external_id,
            status=status,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def list_events(self, user_id: str) -> list[BillingEvent]:
        res = await self.db.execute(select(BillingEvent).where(BillingEvent.user_id == user_id))
        return list(res.scalars().all())
