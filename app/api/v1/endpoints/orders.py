"""Order management endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.schemas.order import OrderCreate, OrderOut, OrderList
from app.dependencies import get_current_user
from app.services.order_service import OrderService

router = APIRouter()

@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    order_data: OrderCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new order and initiate payment.
    
    **Flow**:
    1. Validates ticket availability
    2. Locks inventory
    3. Creates order
    4. Creates Stripe payment intent
    5. Returns order with payment details
    
    **Requires**: Authenticated user
    """
    service = OrderService(db)
    return await service.create_order(current_user.id, order_data)

@router.get("", response_model=List[OrderList])
async def list_orders(
    skip: int = 0,
    limit: int = 20,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's orders.
    
    Returns all orders for the authenticated user, sorted by creation date.
    """
    service = OrderService(db)
    return await service.list_user_orders(current_user.id)

@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get order details including items."""
    service = OrderService(db)
    return await service.get_order(order_id, current_user.id)

@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: UUID,
    reason: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel pending order.
    
    Restores ticket inventory and event capacity.
    **Note**: Cannot cancel confirmed orders - use refund instead.
    """
    service = OrderService(db)
    return await service.cancel_order(order_id, current_user.id, reason)

@router.get("/{order_id}/tickets")
async def download_tickets(
    order_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get download URL for tickets PDF.
    
    Returns presigned URL valid for 1 hour.
    **Requires**: Order must be paid (payment_status = 'succeeded').
    """
    service = OrderService(db)
    return await service.get_ticket_download_url(order_id, current_user.id)