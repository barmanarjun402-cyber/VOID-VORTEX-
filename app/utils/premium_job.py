from datetime import UTC, datetime

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.models.user import User
from app.db.session import SessionLocal

logger = get_logger(__name__)


async def downgrade_expired_premium() -> int:
    changed = 0
    async with SessionLocal() as db:
        rows = list(
            (
                await db.execute(
                    select(User).where(
                        User.tier.in_(["premium", "business"]),
                        User.premium_expires_at.is_not(None),
                        User.premium_expires_at < datetime.now(UTC),
                    )
                )
            )
            .scalars()
            .all()
        )
        for user in rows:
            user.tier = "free"
            user.premium_expires_at = None
            changed += 1
        if changed:
            await db.commit()
    if changed:
        logger.info("premium_users_downgraded", count=changed)
    return changed
