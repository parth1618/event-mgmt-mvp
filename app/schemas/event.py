"""Event schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.constants import EventStatus


class EventBase(BaseModel):
    """Base event schema."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    start_datetime: datetime
    end_datetime: datetime
    venue_name: str = Field(..., min_length=1, max_length=255)
    venue_address: str = Field(..., min_length=1, max_length=500)
    venue_city: str = Field(..., min_length=1, max_length=100)
    venue_state: str | None = Field(None, max_length=100)
    venue_country: str = Field(..., min_length=1, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    category_id: UUID

    @field_validator("end_datetime")
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        """Validate end datetime is after start datetime."""
        if "start_datetime" in info.data and v <= info.data["start_datetime"]:
            raise ValueError("End datetime must be after start datetime")
        return v


class EventCreate(EventBase):
    """Schema for creating event."""

    pass


class EventUpdate(BaseModel):
    """Schema for updating event."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    venue_city: str | None = None
    venue_state: str | None = None
    venue_country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    category_id: UUID | None = None


class EventOut(EventBase):
    """Schema for event response."""

    id: UUID
    slug: str
    banner_url: str | None = None
    total_capacity: int
    available_capacity: int
    status: EventStatus
    is_featured: bool
    organizer_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventList(BaseModel):
    """Schema for event list item."""

    id: UUID
    title: str
    slug: str
    start_datetime: datetime
    venue_city: str
    venue_country: str
    banner_url: str | None = None
    status: EventStatus
    available_capacity: int
    is_featured: bool

    model_config = {"from_attributes": True}


class EventSearch(BaseModel):
    """Schema for event search/filter."""

    q: str | None = None  # Search query
    category_id: UUID | None = None
    date_gte: datetime | None = None
    date_lte: datetime | None = None
    location: str | None = None  # City or country
    price_lte: float | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
