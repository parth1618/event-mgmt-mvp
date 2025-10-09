"""Ticket management endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketOut, TicketAvailability
from app.dependencies import get_current_organizer, get_current_user
from app.services.ticket_service import TicketService

router = APIRouter()

@router.post("/events/{event_id}/tickets", response_model=TicketOut, status_code=201)
async def create_ticket(
    event_id: UUID,
    ticket_data: TicketCreate,
    current_user = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Create ticket type for event.
    
    **Requires**: Organizer role
    """
    service = TicketService(db)
    return await service.create_ticket(event_id, current_user.id, ticket_data)

@router.get("/events/{event_id}/tickets", response_model=List[TicketOut])
async def list_tickets(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all tickets for an event.
    
    **Public endpoint** - no authentication required.
    """
    service = TicketService(db)
    return await service.list_tickets(event_id)

@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get ticket details."""
    service = TicketService(db)
    from app.repositories.ticket import TicketRepository
    ticket = await TicketRepository(db).get(ticket_id)
    if not ticket:
        from fastapi import HTTPException
        raise HTTPException(404, "Ticket not found")
    return ticket

@router.get("/{ticket_id}/availability", response_model=TicketAvailability)
async def check_availability(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Check ticket availability.
    
    Returns real-time availability status.
    """
    service = TicketService(db)
    return await service.check_availability(ticket_id)

@router.put("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    current_user = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Update ticket details.
    
    **Requires**: Organizer role and ownership of event.
    """
    service = TicketService(db)
    return await service.update_ticket(ticket_id, current_user.id, ticket_data)

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: UUID,
    current_user = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Delete ticket type.
    
    **Requires**: Organizer role and ownership of event.
    **Note**: Cannot delete tickets with existing orders.
    """
    from app.repositories.ticket import TicketRepository
    from fastapi import HTTPException
    
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get(ticket_id)
    
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    
    # Check ownership
    from app.repositories.event import EventRepository
    event = await EventRepository(db).get(ticket.event_id)
    if event.organizer_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    # Check if ticket has orders
    if ticket.quantity_total - ticket.quantity_available > 0:
        raise HTTPException(400, "Cannot delete ticket with existing orders")
    
    await ticket_repo.delete(ticket_id)
    return None