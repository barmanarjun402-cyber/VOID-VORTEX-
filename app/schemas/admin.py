from datetime import datetime

from pydantic import BaseModel


class UserTierUpdate(BaseModel):
    tier: str
    premium_expires_at: datetime | None = None


class BanUserRequest(BaseModel):
    banned: bool
