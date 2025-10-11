"""Event model for event management."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.utils.constants import EventStatus


class Event(Base):
    """Event model for managing events.

    Attributes:
        id: Unique event identifier (UUID).
        title: Event title.
        description: Event description.
        slug: URL-friendly slug.
        start_datetime: Event start time (UTC).
        end_datetime: Event end time (UTC).
        venue_name: Venue name.
        venue_address: Venue address.
        venue_city: Venue city.
        venue_state: Venue state/province.
        venue_country: Venue country.
        latitude: Venue latitude (for future geo search).
        longitude: Venue longitude (for future geo search).
        banner_url: Event banner image URL.
        total_capacity: Total event capacity.
        available_capacity: Available capacity.
        status: Event status (DRAFT, PUBLISHED, CANCELLED).
        is_featured: Whether event is featured.
        organizer_id: Foreign key to organizer user.
        category_id: Foreign key to category.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    venue_name: Mapped[str] = mapped_column(String(255), nullable=False)
    venue_address: Mapped[str] = mapped_column(String(500), nullable=False)
    venue_city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    venue_state: Mapped[str] = mapped_column(String(100), nullable=True)
    venue_country: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)

    banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus), nullable=False, default=EventStatus.DRAFT, index=True
    )
    is_featured: Mapped[bool] = mapped_column(default=False, nullable=False)

    organizer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

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
    organizer: Mapped["User"] = relationship("User", back_populates="events")  # type: ignore # noqa: F821
    category: Mapped["Category"] = relationship("Category", back_populates="events")  # type: ignore # noqa: F821
    tickets: Mapped[list["Ticket"]] = relationship(  # type: ignore # noqa: F821
        "Ticket", back_populates="event", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(  # type: ignore # noqa: F821
        "Order", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of Event."""
        return f"<Event(id={self.id}, title={self.title}, status={self.status})>"
