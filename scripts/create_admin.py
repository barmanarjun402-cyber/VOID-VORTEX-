import asyncio

from sqlalchemy import select

from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.user_service import UserService


async def main() -> None:
    async with SessionLocal() as db:
        service = UserService(db)
        existing = await db.scalar(select(User).where(User.email == "admin@voidvortex.io"))
        if existing:
            print("Admin already exists")
            return
        user = await service.create_user("admin@voidvortex.io", "ChangeThisPassword123!")
        user.tier = "admin"
        await db.commit()
        print(f"Created admin user {user.email}")


if __name__ == "__main__":
    asyncio.run(main())
