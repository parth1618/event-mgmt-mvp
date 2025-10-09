"""Order schemas."""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.utils.constants import OrderStatus, PaymentStatus


class OrderItemCreate(BaseModel):
    """Schema for creating order item."""
    
    ticket_id: UUID
    quantity: int = Field(..., gt=0)


class OrderItemOut(BaseModel):
    """Schema for order item response."""
    
    id: UUID
    ticket_id: UUID
    quantity: int
    unit_price: float
    subtotal: float
    
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    """Schema for creating order."""
    
    event_id: UUID
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderOut(BaseModel):
    """Schema for order response."""
    
    id: UUID
    order_number: str
    user_id: UUID
    event_id: UUID
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    items: List[OrderItemOut]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class OrderList(BaseModel):
    """Schema for order list item."""
    
    id: UUID
    order_number: str
    event_id: UUID
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    
    model_config = {"from_attributes": True}