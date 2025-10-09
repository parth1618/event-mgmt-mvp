"""Ticket type model for event ticketing."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class Ticket(Base):
    """Ticket type model (e.g., General Admission, VIP).
    
    Attributes:
        id: Unique ticket type identifier (UUID).
        event_id: Foreign key to event.
        name: Ticket type name (e.g., "General Admission").
        description: Ticket description.
        price: Ticket price.
        quantity_total: Total tickets available.
        quantity_available: Remaining tickets.
        min_per_order: Minimum tickets per order.
        max_per_order: Maximum tickets per order.
        sale_start: Sale start datetime.
        sale_end: Sale end datetime.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """
    
    __tablename__ = "tickets"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_total: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False)
    min_per_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_per_order: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    sale_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    sale_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="tickets")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="ticket"
    )
    
    def __repr__(self) -> str:
        """String representation of Ticket."""
        return f"<Ticket(id={self.id}, name={self.name}, price={self.price})>"