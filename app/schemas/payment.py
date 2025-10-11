"""Payment schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.utils.constants import PaymentStatus


class PaymentIntentCreate(BaseModel):
    """Schema for creating payment intent."""

    order_id: UUID


class PaymentConfirm(BaseModel):
    """Schema for confirming payment."""

    payment_intent_id: str


class PaymentOut(BaseModel):
    """Schema for payment response."""

    id: UUID
    order_id: UUID
    stripe_payment_intent_id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentRefund(BaseModel):
    """Schema for payment refund request."""

    reason: str | None = None


class StripeWebhookEvent(BaseModel):
    """Schema for Stripe webhook event."""

    id: str
    type: str
    data: dict
