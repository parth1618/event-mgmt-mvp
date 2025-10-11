"""Ticket repository."""

from uuid import UUID

from sqlalchemy import select

from app.models.ticket import Ticket
from app.repositories.base import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    """Repository for Ticket model."""

    def __init__(self, db):
        super().__init__(Ticket, db)

    async def get_by_event(self, event_id: UUID) -> list[Ticket]:
        """Get all tickets for an event.

        Args:
            event_id: Event UUID.

        Returns:
            list[Ticket]: Event tickets.
        """
        result = await self.db.execute(
            select(Ticket).where(Ticket.event_id == event_id).order_by(Ticket.price.asc())
        )
        return list(result.scalars().all())

    async def get_available(self, ticket_id: UUID) -> Ticket | None:
        """Get ticket with lock for update (inventory control).

        Args:
            ticket_id: Ticket UUID.

        Returns:
            Ticket| None: Ticket if available.
        """
        result = await self.db.execute(
            select(Ticket).where(Ticket.id == ticket_id).with_for_update()
        )
        return result.scalar_one_or_none()
