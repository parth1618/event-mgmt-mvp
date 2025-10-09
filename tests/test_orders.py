"""Order endpoint tests."""

import pytest
from datetime import datetime, timedelta

@pytest.fixture
async def test_ticket(test_db, test_event):
    """Create test ticket."""
    from app.models.ticket import Ticket
    from decimal import Decimal
    
    ticket = Ticket(
        event_id=test_event.id,
        name="Test Ticket",
        price=Decimal("50.00"),
        quantity_total=100,
        quantity_available=100,
        min_per_order=1,
        max_per_order=5
    )
    test_db.add(ticket)
    await test_db.commit()
    await test_db.refresh(ticket)
    return ticket

def test_create_order(client: TestClient, test_user, test_event, test_ticket):
    """Test order creation."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create order
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": str(test_event.id),
            "items": [
                {
                    "ticket_id": str(test_ticket.id),
                    "quantity": 2
                }
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_amount"] == 100.00  # 2 tickets * $50
    assert data["status"] == "pending"
    assert len(data["items"]) == 1

def test_create_order_insufficient_stock(client: TestClient, test_user, test_event, test_ticket):
    """Test order creation with insufficient stock."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to order more than available
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": str(test_event.id),
            "items": [
                {
                    "ticket_id": str(test_ticket.id),
                    "quantity": 200  # More than available
                }
            ]
        }
    )
    assert response.status_code == 400
    assert "insufficient" in response.json()["detail"].lower()

def test_list_user_orders(client: TestClient, test_user):
    """Test listing user's orders."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List orders
    response = client.get("/api/v1/orders", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_cancel_order(client: TestClient, test_user, test_event, test_ticket):
    """Test order cancellation."""
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "TestPass123!"
        }
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create order
    create_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": str(test_event.id),
            "items": [
                {
                    "ticket_id": str(test_ticket.id),
                    "quantity": 2
                }
            ]
        }
    )
    order_id = create_response.json()["id"]
    
    # Cancel order
    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"