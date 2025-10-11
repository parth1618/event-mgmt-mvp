"""Event management service."""

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.repositories.category import CategoryRepository
from app.repositories.event import EventRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.event import EventCreate, EventUpdate
from app.services.storage_service import storage_service
from app.utils.constants import ALLOWED_IMAGE_MIMES
from app.utils.helpers import slugify


class EventService:
    """Service for event management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize event service."""
        self.db = db
        self.event_repo = EventRepository(db)
        self.category_repo = CategoryRepository(db)

    async def create_event(self, organizer_id: UUID, event_data: EventCreate) -> Event:
        """Create new event."""
        # Validate category exists
        category = await self.category_repo.get(event_data.category_id)
        if not category:
            raise HTTPException(404, "Category not found")

        # Validate dates
        if event_data.end_datetime <= event_data.start_datetime:
            raise HTTPException(400, "End date must be after start date")

        if event_data.start_datetime < datetime.utcnow():
            raise HTTPException(400, "Event cannot start in the past")

        # Generate slug from title
        slug = slugify(event_data.title)

        # Create event
        event = await self.event_repo.create(
            title=event_data.title,
            description=event_data.description,
            slug=slug,
            category_id=event_data.category_id,
            organizer_id=organizer_id,
            start_datetime=event_data.start_datetime,
            end_datetime=event_data.end_datetime,
            venue_name=event_data.venue_name,
            venue_address=event_data.venue_address,
            venue_city=event_data.venue_city,
            venue_state=event_data.venue_state,
            venue_country=event_data.venue_country,
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            total_capacity=0,  # Will be updated when tickets are added
            available_capacity=0,
            status="draft",
        )

        logger.info(f"Event created: {event.title} by organizer: {organizer_id}")
        return event

    async def search_events(
        self,
        q: str | None = None,
        category_id: UUID | None = None,
        date_gte: str | None = None,
        date_lte: str | None = None,
        location: str | None = None,
        price_lte: float | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse:
        """Search events with filters and pagination."""
        # Parse dates
        start_date = None
        end_date = None
        if date_gte:
            try:
                start_date = datetime.fromisoformat(date_gte.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(400, "Invalid date_gte format")

        if date_lte:
            try:
                end_date = datetime.fromisoformat(date_lte.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(400, "Invalid date_lte format")

        # Calculate skip
        skip = (page - 1) * size

        # Search events
        events = await self.event_repo.search(
            query=q,
            category_id=category_id,
            location=location,
            start_date=start_date,
            end_date=end_date,
            min_price=None,
            max_price=price_lte,
            status="published",
            skip=skip,
            limit=size,
        )

        # Get total count
        total = await self.event_repo.count(status="published")

        # Calculate pagination metadata
        total_pages = (total + size - 1) // size

        return PaginatedResponse(
            success=True,
            data=events,
            pagination=PaginationMeta(total=total, page=page, size=size, pages=total_pages),
        )

    async def get_event(self, event_id: UUID) -> Event:
        """Get event by ID."""
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(404, "Event not found")
        return event

    async def update_event(
        self, event_id: UUID, organizer_id: UUID, event_data: EventUpdate
    ) -> Event:
        """Update event."""
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(404, "Event not found")

        # Check authorization
        if event.organizer_id != organizer_id:
            raise HTTPException(403, "Not authorized to update this event")

        # Validate dates if provided
        update_data = event_data.dict(exclude_unset=True)

        if "end_datetime" in update_data and "start_datetime" not in update_data:
            if update_data["end_datetime"] <= event.start_datetime:
                raise HTTPException(400, "End date must be after start date")

        if "start_datetime" in update_data and "end_datetime" in update_data:
            if update_data["end_datetime"] <= update_data["start_datetime"]:
                raise HTTPException(400, "End date must be after start date")

        # Update event
        updated_event = await self.event_repo.update(event_id, **update_data)

        logger.info(f"Event updated: {event.title}")
        return updated_event

    async def delete_event(self, event_id: UUID, organizer_id: UUID) -> None:
        """Delete event."""
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(404, "Event not found")

        # Check authorization
        if event.organizer_id != organizer_id:
            raise HTTPException(403, "Not authorized to delete this event")

        # Check if event has orders
        if event.orders and len(event.orders) > 0:
            raise HTTPException(400, "Cannot delete event with existing orders")

        # Delete event
        await self.event_repo.delete(event_id)
        logger.info(f"Event deleted: {event.title}")

    async def publish_event(self, event_id: UUID, organizer_id: UUID) -> Event:
        """Publish event."""
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(404, "Event not found")

        # Check authorization
        if event.organizer_id != organizer_id:
            raise HTTPException(403, "Not authorized")

        # Validate event has tickets
        if not event.tickets or len(event.tickets) == 0:
            raise HTTPException(400, "Cannot publish event without tickets")

        # Calculate total capacity from tickets
        total_capacity = sum(ticket.quantity_total for ticket in event.tickets)

        # Publish event
        updated_event = await self.event_repo.update(
            event_id,
            status="published",
            published_at=datetime.utcnow(),
            total_capacity=total_capacity,
            available_capacity=total_capacity,
        )

        logger.info(f"Event published: {event.title}")
        return updated_event

    async def upload_banner(self, event_id: UUID, organizer_id: UUID, file: UploadFile) -> Event:
        """Upload event banner."""
        event = await self.event_repo.get(event_id)
        if not event:
            raise HTTPException(404, "Event not found")

        # Check authorization
        if event.organizer_id != organizer_id:
            raise HTTPException(403, "Not authorized")

        # Delete old banner if exists
        if event.banner_url:
            await storage_service.delete_file(event.banner_url)

        # Upload new banner
        banner_url = await storage_service.upload_file(
            file, folder="banners", allowed_types=ALLOWED_IMAGE_MIMES
        )

        # Update event
        updated_event = await self.event_repo.update(event_id, banner_url=banner_url)

        logger.info(f"Banner uploaded for event: {event.title}")
        return updated_event
