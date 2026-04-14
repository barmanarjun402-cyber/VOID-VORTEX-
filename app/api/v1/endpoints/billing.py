from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.billing import BillingWebhookPayload
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/webhook")
async def billing_webhook(
    payload: BillingWebhookPayload,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    x_signature: str | None = Header(default=None),
):
    settings = get_settings()
    valid = x_signature in {settings.stripe_webhook_secret, settings.razorpay_webhook_secret}
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    await BillingService(db).record_event(
        user_id=payload.user_id,
        provider=payload.provider,
        event_type=payload.event_type,
        external_id=payload.event_id,
        status=payload.status,
    )
    return {"ok": True}


@router.get("/events")
async def list_billing_events(
    user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db_session)]
):
    events = await BillingService(db).list_events(user.id)
    return [
        {
            "provider": e.provider,
            "event_type": e.event_type,
            "status": e.status,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
