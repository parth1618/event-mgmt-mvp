"""Payment model for Stripe transactions."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.utils.constants import PaymentStatus


class Payment(Base):
    """Payment model for tracking Stripe transactions.

    Attributes:
        id: Unique payment identifier (UUID).
        order_id: Foreign key to order (unique).
        stripe_payment_intent_id: Stripe PaymentIntent ID.
        amount: Payment amount.
        currency: Payment currency.
        status: Payment status.
        payment_method: Payment method type.
        created_at: Payment creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    stripe_payment_intent_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payment")  # type: ignore # noqa: F821

    def __repr__(self) -> str:
        """String representation of Payment."""
        return f"<Payment(id={self.id}, stripe_id={self.stripe_payment_intent_id}, status={self.status})>"
