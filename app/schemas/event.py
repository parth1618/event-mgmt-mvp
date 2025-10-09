"""Event schemas."""

from typing import Optional, List
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
    venue_state: Optional[str] = Field(None, max_length=100)
    venue_country: str = Field(..., min_length=1, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
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
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    venue_city: Optional[str] = None
    venue_state: Optional[str] = None
    venue_country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category_id: Optional[UUID] = None


class EventOut(EventBase):
    """Schema for event response."""
    
    id: UUID
    slug: str
    banner_url: Optional[str] = None
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
    banner_url: Optional[str] = None
    status: EventStatus
    available_capacity: int
    is_featured: bool
    
    model_config = {"from_attributes": True}


class EventSearch(BaseModel):
    """Schema for event search/filter."""
    
    q: Optional[str] = None  # Search query
    category_id: Optional[UUID] = None
    date_gte: Optional[datetime] = None
    date_lte: Optional[datetime] = None
    location: Optional[str] = None  # City or country
    price_lte: Optional[float] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)