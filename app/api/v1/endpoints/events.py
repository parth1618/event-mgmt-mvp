"""Event management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.event import EventCreate, EventUpdate, EventOut, EventList
from app.schemas.common import PaginatedResponse
from app.dependencies import get_current_user, get_current_organizer
from app.models.user import User
from app.services.event_service import EventService

router = APIRouter()


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    """Create a new event (organizer only).
    
    Args:
        event_data: Event creation data.
        current_user: Current authenticated organizer.
        db: Database session.
        
    Returns:
        EventOut: Created event data.
        
    Example:
        curl -X POST "http://localhost:8000/api/v1/events" \\
             -H "Authorization: Bearer <token>" \\
             -H "Content-Type: application/json" \\
             -d '{"title": "Tech Conference 2024", ...}'
    """
    event_service = EventService(db)
    event = await event_service.create_event(current_user.id, event_data)
    return event


@router.get("", response_model=PaginatedResponse[EventList])
async def list_events(
    q: str = Query(None, description="Search query"),
    category_id: UUID = Query(None),
    date_gte: str = Query(None),
    date_lte: str = Query(None),
    location: str = Query(None),
    price_lte: float = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[EventList]:
    """List and search events with filters and pagination.
    
    Args:
        q: Search query (title, description).
        category_id: Filter by category.
        date_gte: Filter events starting from date.
        date_lte: Filter events ending before date.
        location: Filter by city or country.
        price_lte: Filter by maximum price.
        page: Page number.
        size: Items per page.
        db: Database session.
        
    Returns:
        PaginatedResponse: Paginated list of events.
    """
    event_service = EventService(db)
    result = await event_service.search_events(
        q=q,
        category_id=category_id,
        date_gte=date_gte,
        date_lte=date_lte,
        location=location,
        price_lte=price_lte,
        page=page,
        size=size,
    )
    return result


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    """Get event details by ID.
    
    Args:
        event_id: Event UUID.
        db: Database session.
        
    Returns:
        EventOut: Event data.
        
    Raises:
        HTTPException: If event not found.
    """
    event_service = EventService(db)
    event = await event_service.get_event(event_id)
    return event


@router.put("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: UUID,
    event_update: EventUpdate,
    current_user: User = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    """Update event (organizer only, own events).
    
    Args:
        event_id: Event UUID.
        event_update: Updated event data.
        current_user: Current authenticated organizer.
        db: Database session.
        
    Returns:
        EventOut: Updated event data.
        
    Raises:
        HTTPException: If event not found or unauthorized.
    """
    event_service = EventService(db)
    event = await event_service.update_event(event_id, current_user.id, event_update)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete event (organizer only, own events).
    
    Args:
        event_id: Event UUID.
        current_user: Current authenticated organizer.
        db: Database session.
        
    Raises:
        HTTPException: If event not found or unauthorized.
    """
    event_service = EventService(db)
    await event_service.delete_event(event_id, current_user.id)


@router.patch("/{event_id}/publish", response_model=EventOut)
async def publish_event(
    event_id: UUID,
    current_user: User = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    """Publish event (make it visible to attendees).
    
    Args:
        event_id: Event UUID.
        current_user: Current authenticated organizer.
        db: Database session.
        
    Returns:
        EventOut: Updated event data.
    """
    event_service = EventService(db)
    event = await event_service.publish_event(event_id, current_user.id)
    return event


@router.post("/{event_id}/banner", response_model=EventOut)
async def upload_banner(
    event_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
) -> EventOut:
    """Upload event banner image.
    
    Args:
        event_id: Event UUID.
        file: Banner image file (JPEG, PNG, max 5MB).
        current_user: Current authenticated organizer.
        db: Database session.
        
    Returns:
        EventOut: Updated event data with banner URL.
    """
    event_service = EventService(db)
    event = await event_service.upload_banner(event_id, current_user.id, file)
    return event