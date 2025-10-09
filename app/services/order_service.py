"""Order service with inventory management and transactions."""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from loguru import logger

from app.repositories.order import OrderRepository
from app.repositories.ticket import TicketRepository
from app.repositories.event import EventRepository
from app.models.order import Order, OrderItem
from app.models.ticket import Ticket
from app.schemas.order import OrderCreate, OrderOut
from app.utils.helpers import generate_order_number
from app.utils.constants import OrderStatus, PaymentStatus

class InsufficientStockException(HTTPException):
    """Exception for insufficient ticket stock."""
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)

class OrderService:
    """Service for order management with inventory control."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.ticket_repo = TicketRepository(db)
        self.event_repo = EventRepository(db)
    
    async def create_order(
        self,
        user_id: UUID,
        order_data: OrderCreate
    ) -> Order:
        """Create order with inventory checks and transaction handling."""
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
                result = await self.db.execute(
                    select(Ticket)
                    .where(Ticket.id == item.ticket_id)
                    .with_for_update()
                )
                ticket = result.scalar_one_or_none()
                
                if not ticket:
                    raise HTTPException(404, f"Ticket {item.ticket_id} not found")
                
                if ticket.event_id != order_data.event_id:
                    raise HTTPException(400, "Ticket does not belong to this event")
                
                # Check availability
                if ticket.quantity_available < item.quantity:
                    raise InsufficientStockException(
                        f"Insufficient stock for {ticket.name}. Available: {ticket.quantity_available}"
                    )
                
                # Check min/max per order
                if item.quantity < ticket.min_per_order:
                    raise HTTPException(400, f"Minimum {ticket.min_per_order} tickets required")
                
                if item.quantity > ticket.max_per_order:
                    raise HTTPException(400, f"Maximum {ticket.max_per_order} tickets allowed")
                
                # Calculate subtotal
                subtotal = float(ticket.price) * item.quantity
                total_amount += subtotal
                
                # Update ticket inventory
                ticket.quantity_available -= item.quantity
                
                order_items_data.append({
                    "ticket_id": ticket.id,
                    "quantity": item.quantity,
                    "unit_price": float(ticket.price),
                    "subtotal": subtotal
                })
            
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
                payment_status=PaymentStatus.PENDING
            )
            self.db.add(order)
            await self.db.flush()  # Get order ID
            
            # Create order items
            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                self.db.add(order_item)
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Order created: {order.order_number}, amount: {total_amount}")
            
            # Trigger payment intent creation
            from app.services.payment_service import PaymentService
            payment_service = PaymentService(self.db)
            await payment_service.create_payment_intent(order.id, user_id)
            
            return order
    
    async def list_user_orders(self, user_id: UUID) -> List[Order]:
        """Get all orders for a user."""
        return await self.order_repo.get_by_user(user_id)
    
    async def get_order(self, order_id: UUID, user_id: UUID) -> Order:
        """Get order details."""
        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise HTTPException(404, "Order not found")
        
        if order.user_id != user_id:
            raise HTTPException(403, "Not authorized")
        
        return order
    
    async def get_ticket_download_url(
        self,
        order_id: UUID,
        user_id: UUID
    ) -> dict:
        """Get presigned URL for downloading tickets PDF."""
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
        url = storage_service.get_presigned_url(key, expiration=3600)
        
        return {
            "download_url": url,
            "expires_in": 3600,
            "order_number": order.order_number
        }
    
    async def cancel_order(
        self,
        order_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Order:
        """Cancel order and restore inventory."""
        order = await self.order_repo.get_with_items(order_id)
        if not order:
            raise HTTPException(404, "Order not found")
        
        if order.user_id != user_id:
            raise HTTPException(403, "Not authorized")
        
        if order.status == OrderStatus.CONFIRMED:
            raise HTTPException(400, "Cannot cancel confirmed order. Request refund instead.")
        
        if order.status == OrderStatus.CANCELLED:
            raise HTTPException(400, "Order already cancelled")
        
        # Start transaction
        async with self.db.begin():
            # Restore ticket inventory
            for item in order.items:
                ticket = await self.ticket_repo.get(item.ticket_id)
                ticket.quantity_available += item.quantity
            
            # Restore event capacity
            event = await self.event_repo.get(order.event_id)
            total_tickets = sum(item.quantity for item in order.items)
            event.available_capacity += total_tickets
            
            # Update order status
            await self.order_repo.update(
                order_id,
                status=OrderStatus.CANCELLED
            )
            
            await self.db.commit()
        
        logger.info(f"Order cancelled: {order.order_number}, reason: {reason}")
        return await self.order_repo.get(order_id)SUCCEEDED,
                payment_method=payment_intent.get('payment_method')
            )
            
            # Update order status
            await self.order_repo.update(
                UUID(order_id),
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.SUCCEEDED
            )
            
            # Trigger ticket generation task
            from app.tasks.tasks import generate_ticket_pdf
            generate_ticket_pdf.delay(order_id)
            
            # Send confirmation email
            from app.services.email_service import email_service
            order = await self.order_repo.get(UUID(order_id))
            await email_service.send_order_confirmation(
                to=order.user.email,
                order_number=order.order_number,
                event_title=order.event.title,
                total_amount=order.total_amount
            )
            
            logger.info(f"Payment succeeded for order: {order_id}")