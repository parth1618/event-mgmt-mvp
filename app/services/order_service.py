"""Order service with inventory management and transactions."""

import hashlib
from uuid import UUID

from fastapi import HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.core.exceptions import InsufficientStockException
from app.models.order import Order
from app.models.order_item import OrderItem
from app.repositories.event import EventRepository
from app.repositories.order import OrderRepository
from app.repositories.ticket import TicketRepository
from app.schemas.order import OrderCreate
from app.utils.constants import OrderStatus, PaymentStatus
from app.utils.helpers import generate_order_number


class OrderService:
    """Service for order management with inventory control."""

    def __init__(self, db: AsyncSession):
        """Initialize order service.

        Args:
            db: Database session.
        """
        self.db = db
        self.order_repo = OrderRepository(db)
        self.ticket_repo = TicketRepository(db)
        self.event_repo = EventRepository(db)

    async def _check_idempotency(
        self, user_id: UUID, event_id: UUID, items_hash: str
    ) -> Order | None:
        """Check if identical order already exists (prevent duplicates)."""
        idempotency_key = f"order_idempotency:{user_id}:{event_id}:{items_hash}"
        cached_order_id = await cache_manager.get(idempotency_key)

        if cached_order_id:
            order = await self.order_repo.get(UUID(cached_order_id))
            if order:
                logger.info(f"Order already exists (idempotency): {order.id}")
                return order

        return None

    async def create_order(self, user_id: UUID, order_data: OrderCreate) -> Order:
        """Create order with inventory checks and transaction handling.

        Args:
            user_id: User ID creating the order.
            order_data: Order creation data.

        Returns:
            Order: Created order with items.

        Raises:
            HTTPException: If validation fails.
            InsufficientStockException: If tickets not available.
        """
        # Create hash of order items to detect duplicates
        items_hash = hashlib.md5(
            str([(item.ticket_id, item.quantity) for item in order_data.items]).encode()
        ).hexdigest()

        # Check for duplicate order
        existing_order = await self._check_idempotency(user_id, order_data.event_id, items_hash)
        if existing_order:
            return existing_order

        # Start transaction
        async with self.db.begin():
            # Get event
            event = await self.event_repo.get(order_data.event_id)
            if not event:
                raise HTTPException(404, "Event not found")

            if event.status != "published":
                raise HTTPException(400, "Event not available for booking")

            # Validate and lock tickets
            total_amount = 0.0
            order_items_data = []

            for item in order_data.items:
                # Lock ticket row for update
                ticket = self.ticket_repo.get_available(item.ticket_id)

                if not ticket:
                    raise HTTPException(404, f"Ticket {item.ticket_id} not found")

                if ticket.event_id != order_data.event_id:
                    raise HTTPException(400, "Ticket does not belong to this event")

                # Check availability
                if ticket.quantity_available < item.quantity:
                    raise InsufficientStockException(
                        f"Insufficient stock for {ticket.name}. "
                        f"Available: {ticket.quantity_available}"
                    )

                # Check min/max per order
                if item.quantity < ticket.min_per_order:
                    raise HTTPException(
                        400,
                        f"Minimum {ticket.min_per_order} tickets required for {ticket.name}",
                    )

                if item.quantity > ticket.max_per_order:
                    raise HTTPException(
                        400,
                        f"Maximum {ticket.max_per_order} tickets allowed for {ticket.name}",
                    )

                # Calculate subtotal
                subtotal = float(ticket.price) * item.quantity
                total_amount += subtotal

                # Update ticket inventory
                ticket.quantity_available -= item.quantity

                order_items_data.append(
                    {
                        "ticket_id": ticket.id,
                        "quantity": item.quantity,
                        "unit_price": float(ticket.price),
                        "subtotal": subtotal,
                    }
                )

            # Update event capacity
            total_tickets = sum(item["quantity"] for item in order_items_data)
            event.available_capacity -= total_tickets

            # Create order
            order = Order(
                order_number=generate_order_number(),
                user_id=user_id,
                event_id=order_data.event_id,
                total_amount=total_amount,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
            )
            self.db.add(order)
            await self.db.flush()  # Get order ID

            # Create order items
            for item_data in order_items_data:
                order_item = OrderItem(order_id=order.id, **item_data)
                self.db.add(order_item)

            await self.db.commit()
            await self.db.refresh(order)

            logger.info(
                f"Order created: {order.order_number}, " f"user: {user_id}, amount: ${total_amount}"
            )

            # Create payment intent
            from app.services.payment_service import PaymentService

            payment_service = PaymentService(self.db)
            try:
                await payment_service.create_payment_intent(order.id, user_id)
            except Exception as e:
                logger.error(f"Failed to create payment intent: {e}")
                # Order is still created, payment can be retried

            # After creating order, cache it
            idempotency_key = f"order_idempotency:{user_id}:{order_data.event_id}:{items_hash}"
            await cache_manager.set(idempotency_key, str(order.id), ttl=3600)  # 1 hour

            return order

    async def list_user_orders(self, user_id: UUID, skip: int = 0, limit: int = 20) -> list[Order]:
        """Get all orders for a user.

        Args:
            user_id: User ID.
            skip: Pagination offset.
            limit: Number of orders to return.

        Returns:
            list[Order]: User's orders.
        """
        return await self.order_repo.get_by_user(user_id, skip, limit)

    async def get_order(self, order_id: UUID, user_id: UUID) -> Order:
        """Get order details.

        Args:
            order_id: Order ID.
            user_id: User ID (for authorization).

        Returns:
            Order: Order with items.

        Raises:
            HTTPException: If not found or unauthorized.
        """
        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise HTTPException(404, "Order not found")

        if order.user_id != user_id:
            raise HTTPException(403, "Not authorized")

        return order

    async def cancel_order(self, order_id: UUID, user_id: UUID, reason: str | None = None) -> Order:
        """Cancel order and restore inventory.

        Args:
            order_id: Order ID.
            user_id: User ID (for authorization).
            reason: Cancellation reason.

        Returns:
            Order: Cancelled order.

        Raises:
            HTTPException: If cannot cancel.
        """
        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise HTTPException(404, "Order not found")

        if order.user_id != user_id:
            raise HTTPException(403, "Not authorized")

        if order.status == OrderStatus.CONFIRMED:
            raise HTTPException(400, "Cannot cancel confirmed order. Request refund instead.")

        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(400, "Order already cancelled")

        # Start transaction to restore inventory
        async with self.db.begin():
            # Restore ticket inventory
            for item in order.items:
                ticket = await self.ticket_repo.get(item.ticket_id)
                if ticket:
                    ticket.quantity_available += item.quantity

            # Restore event capacity
            event = await self.event_repo.get(order.event_id)
            if event:
                total_tickets = sum(item.quantity for item in order.items)
                event.available_capacity += total_tickets

            # Update order status
            order.status = OrderStatus.CANCELLED

            await self.db.commit()

        logger.info(f"Order cancelled: {order.order_number}, reason: {reason}")
        return order

    async def get_ticket_download_url(self, order_id: UUID, user_id: UUID) -> dict:
        """Get presigned URL for downloading tickets PDF.

        Args:
            order_id: Order ID.
            user_id: User ID (for authorization).

        Returns:
            dict: Download URL and metadata.

        Raises:
            HTTPException: If unauthorized or not paid.
        """
        order = await self.order_repo.get(order_id)
        if not order:
            raise HTTPException(404, "Order not found")

        if order.user_id != user_id:
            raise HTTPException(403, "Not authorized")

        if order.payment_status != PaymentStatus.SUCCEEDED:
            raise HTTPException(400, "Order not paid")

        # Get presigned URL from storage
        from app.services.storage_service import storage_service

        key = f"tickets/{order_id}.pdf"

        try:
            url = storage_service.get_presigned_url(key, expiration=3600)
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise HTTPException(500, "Failed to generate download URL")

        return {
            "download_url": url,
            "expires_in": 3600,
            "order_number": order.order_number,
        }
