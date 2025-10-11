"""Input validation tests."""

from fastapi.testclient import TestClient


def test_email_validation(client: TestClient):
    """Test email format validation."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid-email", "password": "TestPass123!", "role": "attendee"},
    )
    assert response.status_code == 422


def test_password_strength_validation(client: TestClient):
    """Test password strength requirements."""
    # Too short
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "short", "role": "attendee"},
    )
    assert response.status_code == 422


def test_date_validation(client: TestClient, test_organizer, test_category):
    """Test event date validation."""
    from datetime import datetime, timedelta

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_organizer.email, "password": "OrganizerPass123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # End date before start date
    response = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Invalid Event",
            "description": "Test",
            "category_id": str(test_category.id),
            "start_datetime": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "end_datetime": (datetime.utcnow() + timedelta(days=29)).isoformat(),
            "location": "Test",
            "total_capacity": 100,
        },
    )
    assert response.status_code == 400
