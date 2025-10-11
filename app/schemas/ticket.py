"""Ticket schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TicketBase(BaseModel):
    """Base ticket schema."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(..., ge=0)
    quantity_total: int = Field(..., gt=0)
    min_per_order: int = Field(1, ge=1)
    max_per_order: int = Field(10, ge=1)
    sale_start: datetime | None = None
    sale_end: datetime | None = None


class TicketCreate(TicketBase):
    """Schema for creating ticket type."""

    event_id: UUID


class TicketUpdate(BaseModel):
    """Schema for updating ticket type."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: float | None = Field(None, ge=0)
    quantity_total: int | None = Field(None, gt=0)
    min_per_order: int | None = Field(None, ge=1)
    max_per_order: int | None = Field(None, ge=1)
    sale_start: datetime | None = None
    sale_end: datetime | None = None


class TicketOut(TicketBase):
    """Schema for ticket response."""

    id: UUID
    event_id: UUID
    quantity_available: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketAvailability(BaseModel):
    """Schema for ticket availability response."""

    ticket_id: UUID
    available: bool
    quantity_available: int
    sale_active: bool
