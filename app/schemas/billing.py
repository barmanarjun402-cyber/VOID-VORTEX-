from pydantic import BaseModel


class BillingWebhookPayload(BaseModel):
    provider: str
    event_id: str
    event_type: str
    user_id: str
    status: str
