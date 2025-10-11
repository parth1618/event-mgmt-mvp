"""Category model for event classification."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Category(Base):
    """Event category model.

    Attributes:
        id: Unique category identifier (UUID).
        name: Category name (unique).
        description: Category description.
        slug: URL-friendly slug.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
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
    events: Mapped[list["Event"]] = relationship(  # noqa: F821 # type: ignore
        "Event", back_populates="category"
    )

    def __repr__(self) -> str:
        """String representation of Category."""
        return f"<Category(id={self.id}, name={self.name})>"
