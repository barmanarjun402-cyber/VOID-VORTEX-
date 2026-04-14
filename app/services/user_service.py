from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models.user import User

TIER_LIMITS = {
    "free": 1,
    "premium": 5,
    "business": 20,
    "admin": 9999,
}


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, email: str, password: str) -> User:
        user = User(email=email.lower().strip(), password_hash=hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        res = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        return res.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def check_bot_limit(self, user: User, current_count: int) -> bool:
        if user.tier in ("premium", "business") and user.premium_expires_at and user.premium_expires_at < datetime.now(UTC):
            user.tier = "free"
            user.premium_expires_at = None
            await self.db.commit()
        return current_count < TIER_LIMITS.get(user.tier, 1)
