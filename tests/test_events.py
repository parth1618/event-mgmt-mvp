"""Event endpoint tests."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
async def test_category(test_db):
    """Create test category."""
    from app.models.category import Category

    category = Category(
        name="Test Category",
        slug="test-category",
        description="Test category description",
    )
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    return category


@pytest.fixture
async def test_event(test_db, test_organizer, test_category):
    """Create test event."""
    from app.models.event import Event

    event = Event(
        title="Test Event",
        description="Test event description",
        category_id=test_category.id,
        organizer_id=test_organizer.id,
        start_datetime=datetime.utcnow() + timedelta(days=30),
        end_datetime=datetime.utcnow() + timedelta(days=30, hours=2),
        location="Test Location",
        total_capacity=100,
        available_capacity=100,
        status="published",
    )
    test_db.add(event)
    await test_db.commit()
    await test_db.refresh(event)
    return event


def test_create_event(client: TestClient, test_organizer, test_category):
    """Test event creation."""
    # Login as organizer
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_organizer.email, "password": "OrganizerPass123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create event
    start_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=30, hours=2)).isoformat()

    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "New Test Event",
            "description": "Event description",
            "category_id": str(test_category.id),
            "start_datetime": start_date,
            "end_datetime": end_date,
            "location": "Test Venue",
            "total_capacity": 200,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Test Event"
    assert data["status"] == "draft"


def test_search_events(client: TestClient, test_event):
    """Test event search."""
    response = client.get("/api/v1/events/search?query=Test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(event["title"] == "Test Event" for event in data)


def test_get_event(client: TestClient, test_event):
    """Test getting event details."""
    response = client.get(f"/api/v1/events/{test_event.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Event"
    assert data["id"] == str(test_event.id)


def test_update_event(client: TestClient, test_event, test_organizer):
    """Test event update."""
    # Login as organizer
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_organizer.email, "password": "OrganizerPass123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update event
    response = client.put(
        f"/api/v1/events/{test_event.id}",
        headers=headers,
        json={"title": "Updated Event Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Event Title"


def test_publish_event(client: TestClient, test_organizer, test_category):
    """Test event publishing."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_organizer.email, "password": "OrganizerPass123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create draft event
    start_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=30, hours=2)).isoformat()

    create_response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Draft Event",
            "description": "Event description",
            "category_id": str(test_category.id),
            "start_datetime": start_date,
            "end_datetime": end_date,
            "location": "Test Venue",
            "total_capacity": 200,
        },
    )
    event_id = create_response.json()["id"]

    # Publish event
    response = client.post(f"/api/v1/events/{event_id}/publish", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "published"
    assert data["published_at"] is not None
