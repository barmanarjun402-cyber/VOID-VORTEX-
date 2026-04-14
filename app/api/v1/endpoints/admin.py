from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.db.session import get_db_session
from app.schemas.admin import BanUserRequest, UserTierUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    payload: UserTierUpdate,
    admin=Depends(require_admin),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
):
    _ = admin
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.tier = payload.tier
    user.premium_expires_at = payload.premium_expires_at
    await db.commit()
    return {"ok": True}


@router.patch("/users/{user_id}/ban")
async def ban_user(
    user_id: str,
    payload: BanUserRequest,
    admin=Depends(require_admin),
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
):
    _ = admin
    service = UserService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = payload.banned
    await db.commit()
    return {"ok": True}
