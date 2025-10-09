"""Ticket service for ticket management."""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from loguru import logger

from app.repositories.ticket import TicketRepository
from app.repositories.event import EventRepository
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketOut, TicketAvailability
from app.models.ticket import Ticket

class TicketService:
    """Service for ticket operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.event_repo = EventRepository(db)
    
    async def create_ticket(
        self,
        event_id: UUID,
        organizer_id: UUID,
        ticket_data: TicketCreate
    ) -> Ticket:
        """Create ticket type for event."""
        # Verify event ownership
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(404, "Event not found")
        
        if event.organizer_id != organizer_id:
            raise HTTPException(403, "Not authorized to create tickets for this event")
        
        # Validate ticket data
        if ticket_data.min_per_order > ticket_data.max_per_order:
            raise HTTPException(400, "min_per_order cannot exceed max_per_order")
        
        if ticket_data.quantity_total < 1:
            raise HTTPException(400, "Total quantity must be at least 1")
        
        # Create ticket
        ticket = await self.ticket_repo.create(
            event_id=event_id,
            name=ticket_data.name,
            description=ticket_data.description,
            price=ticket_data.price,
            quantity_total=ticket_data.quantity_total,
            quantity_available=ticket_data.quantity_total,
            min_per_order=ticket_data.min_per_order,
            max_per_order=ticket_data.max_per_order,
            sale_start_date=ticket_data.sale_start_date,
            sale_end_date=ticket_data.sale_end_date
        )
        
        logger.info(f"Created ticket: {ticket.id} for event: {event_id}")
        return ticket
    
    async def list_tickets(self, event_id: UUID) -> List[Ticket]:
        """List all tickets for an event."""
        return await self.ticket_repo.get_by_event(event_id)
    
    async def check_availability(self, ticket_id: UUID) -> TicketAvailability:
        """Check ticket availability."""
        ticket = await self.ticket_repo.get(ticket_id)
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        
        return TicketAvailability(
            ticket_id=ticket.id,
            available=ticket.quantity_available > 0,
            quantity_available=ticket.quantity_available,
            quantity_total=ticket.quantity_total
        )
    
    async def update_ticket(
        self,
        ticket_id: UUID,
        organizer_id: UUID,
        ticket_data: TicketUpdate
    ) -> Ticket:
        """Update ticket."""
        ticket = await self.ticket_repo.get(ticket_id)
        if not ticket:
            raise HTTPException(404, "Ticket not found")
        
        # Verify ownership
        event = await self.event_repo.get(ticket.event_id)
        if event.organizer_id != organizer_id:
            raise HTTPException(403, "Not authorized")
        
        # Update fields
        update_data = ticket_data.dict(exclude_unset=True)
        updated = await self.ticket_repo.update(ticket_id, **update_data)
        
        logger.info(f"Updated ticket: {ticket_id}")
        return updated