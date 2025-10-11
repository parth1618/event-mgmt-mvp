"""Repository layer tests."""

from uuid import UUID

import pytest


@pytest.mark.asyncio
async def test_user_repository_create(test_db):
    """Test user repository create."""
    from app.core.security import get_password_hash
    from app.repositories.user import UserRepository

    repo = UserRepository(test_db)
    user = await repo.create(
        email="repo_test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        role="attendee",
    )

    assert user.id is not None
    assert user.email == "repo_test@example.com"
    assert isinstance(user.id, UUID)


@pytest.mark.asyncio
async def test_user_repository_get_by_email(test_db, test_user):
    """Test user repository get by email."""
    from app.repositories.user import UserRepository

    repo = UserRepository(test_db)
    user = await repo.get_by_email(test_user.email)

    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_event_repository_search(test_db, test_event):
    """Test event repository search."""
    from app.repositories.event import EventRepository

    repo = EventRepository(test_db)
    events = await repo.search(query="Test", status="published")

    assert len(events) >= 1
    assert any(e.title == "Test Event" for e in events)


@pytest.mark.asyncio
async def test_ticket_repository_get_available(test_db, test_ticket):
    """Test ticket repository get with lock."""
    from app.repositories.ticket import TicketRepository

    repo = TicketRepository(test_db)
    ticket = await repo.get_available(test_ticket.id)

    assert ticket is not None
    assert ticket.id == test_ticket.id
    assert ticket.quantity_available > 0
