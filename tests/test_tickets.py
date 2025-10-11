"""Ticket endpoint tests."""

from fastapi.testclient import TestClient


def test_create_ticket(client: TestClient, test_event, test_organizer):
    """Test ticket creation."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_organizer.email, "password": "OrganizerPass123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create ticket
    response = client.post(
        f"/api/v1/tickets/events/{test_event.id}/tickets",
        headers=headers,
        json={
            "name": "General Admission",
            "description": "Standard entry ticket",
            "price": 50.00,
            "quantity_total": 100,
            "min_per_order": 1,
            "max_per_order": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "General Admission"
    assert float(data["price"]) == 50.00
    assert data["quantity_available"] == 100


def test_list_tickets(client: TestClient, test_event):
    """Test listing event tickets."""
    response = client.get(f"/api/v1/tickets/events/{test_event.id}/tickets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_check_ticket_availability(client: TestClient, test_event, test_organizer):
    """Test checking ticket availability."""
    # First create a ticket
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": test_organizer.email, "password": "OrganizerPass123!"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        f"/api/v1/tickets/events/{test_event.id}/tickets",
        headers=headers,
        json={
            "name": "VIP",
            "price": 100.00,
            "quantity_total": 20,
            "min_per_order": 1,
            "max_per_order": 2,
        },
    )
    ticket_id = create_response.json()["id"]

    # Check availability
    response = client.get(f"/api/v1/tickets/{ticket_id}/availability")
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["quantity_available"] == 20
