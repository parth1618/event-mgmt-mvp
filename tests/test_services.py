"""Service layer tests."""

import pytest


@pytest.mark.asyncio
async def test_ticket_service_create(test_db, test_event, test_organizer):
    """Test ticket service creation."""
    from decimal import Decimal

    from app.schemas.ticket import TicketCreate
    from app.services.ticket_service import TicketService

    service = TicketService(test_db)
    ticket_data = TicketCreate(
        name="Service Test Ticket",
        price=Decimal("75.00"),
        quantity_total=50,
        min_per_order=1,
        max_per_order=3,
    )

    ticket = await service.create_ticket(test_event.id, test_organizer.id, ticket_data)

    assert ticket.name == "Service Test Ticket"
    assert ticket.price == Decimal("75.00")
    assert ticket.quantity_available == 50


@pytest.mark.asyncio
async def test_order_service_inventory_management(test_db, test_user, test_event, test_ticket):
    """Test order service inventory management."""
    from app.repositories.ticket import TicketRepository
    from app.schemas.order import OrderCreate, OrderItemCreate
    from app.services.order_service import OrderService

    service = OrderService(test_db)
    ticket_repo = TicketRepository(test_db)

    # Get initial quantity
    initial_qty = test_ticket.quantity_available

    # Create order
    order_data = OrderCreate(
        event_id=test_event.id,
        items=[OrderItemCreate(ticket_id=test_ticket.id, quantity=3)],
    )

    order = await service.create_order(test_user.id, order_data)

    # Verify inventory was reduced
    updated_ticket = await ticket_repo.get(test_ticket.id)
    assert updated_ticket.quantity_available == initial_qty - 3
    assert order.total_amount == 150.00  # 3 * $50


@pytest.mark.asyncio
async def test_order_service_cancel_restores_inventory(test_db, test_user, test_event, test_ticket):
    """Test that canceling order restores inventory."""
    from app.repositories.ticket import TicketRepository
    from app.schemas.order import OrderCreate, OrderItemCreate
    from app.services.order_service import OrderService

    service = OrderService(test_db)
    ticket_repo = TicketRepository(test_db)

    initial_qty = test_ticket.quantity_available

    # Create order
    order_data = OrderCreate(
        event_id=test_event.id,
        items=[OrderItemCreate(ticket_id=test_ticket.id, quantity=2)],
    )
    order = await service.create_order(test_user.id, order_data)

    # Cancel order
    await service.cancel_order(order.id, test_user.id)

    # Verify inventory was restored
    updated_ticket = await ticket_repo.get(test_ticket.id)
    assert updated_ticket.quantity_available == initial_qty
