"""Order item model for individual ticket purchases."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class OrderItem(Base):
    """Order item model for ticket line items.

    Attributes:
        id: Unique order item identifier (UUID).
        order_id: Foreign key to order.
        ticket_id: Foreign key to ticket type.
        quantity: Number of tickets.
        unit_price: Price per ticket at time of purchase.
        subtotal: Line item subtotal.
        created_at: Creation timestamp.
    """

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")  # type: ignore # noqa: F821
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="order_items")  # type: ignore # noqa: F821

    def __repr__(self) -> str:
        """String representation of OrderItem."""
        return f"<OrderItem(id={self.id}, quantity={self.quantity}, subtotal={self.subtotal})>"
