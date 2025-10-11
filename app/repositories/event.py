"""Event repository with search capabilities."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    """Repository for Event model."""

    def __init__(self, db):
        super().__init__(Event, db)

    async def search(
        self,
        query: str | None = None,
        category_id: UUID | None = None,
        location: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        status: str | None = "published",
        skip: int = 0,
        limit: int = 20,
    ) -> list[Event]:
        """Search events with filters.

        Args:
            query: Search query for title/description.
            category_id: Filter by category.
            location: Filter by location.
            start_date: Filter by start date (after).
            end_date: Filter by end date (before).
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            status: Event status filter.
            skip: Pagination offset.
            limit: Results limit.

        Returns:
            list[Event]: Matching events.
        """
        stmt = select(Event).options(selectinload(Event.category), selectinload(Event.organizer))

        # Status filter
        if status:
            stmt = stmt.where(Event.status == status)

        # Text search
        if query:
            search_filter = or_(
                Event.title.ilike(f"%{query}%"), Event.description.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)

        # Category filter
        if category_id:
            stmt = stmt.where(Event.category_id == category_id)

        # Location filter
        if location:
            stmt = stmt.where(Event.location.ilike(f"%{location}%"))

        # Date filters
        if start_date:
            stmt = stmt.where(Event.start_datetime >= start_date)
        if end_date:
            stmt = stmt.where(Event.end_datetime <= end_date)

        # Price filters (assuming we join with tickets)
        # This is simplified - in production, you'd join with Ticket model

        # Ordering and pagination
        stmt = stmt.order_by(Event.start_datetime.asc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_organizer(
        self, organizer_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[Event]:
        """Get events by organizer.

        Args:
            organizer_id: Organizer user ID.
            skip: Pagination offset.
            limit: Results limit.

        Returns:
            list[Event]: Organizer's events.
        """
        result = await self.db.execute(
            select(Event)
            .where(Event.organizer_id == organizer_id)
            .order_by(Event.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
