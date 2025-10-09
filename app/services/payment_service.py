"""Stripe payment integration service."""

from typing import Optional
from uuid import UUID
import stripe
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.config import settings
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.models.payment import Payment
from app.utils.constants import PaymentStatus, OrderStatus

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    """Service for handling Stripe payments."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.payment_repo = PaymentRepository(db)
    
    async def create_payment_intent(
        self,
        order_id: UUID,
        user_id: UUID
    ) -> Payment:
        """Create Stripe payment intent for order."""
        # Get order
        order = await self.order_repo.get(order_id)
        if not order:
            raise HTTPException(404, "Order not found")
        
        if order.user_id != user_id:
            raise HTTPException(403, "Not authorized")
        
        # Check if payment already exists
        existing_payment = await self.payment_repo.get_by_order(order_id)
        if existing_payment:
            raise HTTPException(400, "Payment already exists for this order")
        
        try:
            # Create Stripe PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Convert to cents
                currency="usd",
                metadata={"order_id": str(order_id)},
                idempotency_key=f"order_{order_id}"
            )
            
            # Create payment record
            payment = await self.payment_repo.create(
                order_id=order_id,
                stripe_payment_intent_id=intent.id,
                amount=order.total_amount,
                currency="usd",
                status=PaymentStatus.PENDING
            )
            
            logger.info(f"Created payment intent: {intent.id} for order: {order_id}")
            return payment
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(400, f"Payment creation failed: {str(e)}")
    
    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(400, "Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(400, "Invalid signature")
        
        # Handle event types
        if event['type'] == 'payment_intent.succeeded':
            await self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            await self._handle_payment_failed(event['data']['object'])
        
        return {"status": "success"}
    
    async def _handle_payment_succeeded(self, payment_intent: dict) -> None:
        """Handle successful payment."""
        intent_id = payment_intent['id']
        order_id = payment_intent['metadata'].get('order_id')
        
        if not order_id:
            logger.error(f"No order_id in payment intent: {intent_id}")
            return
        
        # Update payment status
        payment = await self.payment_repo.get_by_stripe_id(intent_id)
        if payment:
            await self.payment_repo.update(
                payment.id,
                status=PaymentStatus.FAILED
            )
            
            # Update order status
            await self.order_repo.update(
                UUID(order_id),
                payment_status=PaymentStatus.FAILED
            )
            
            logger.warning(f"Payment failed for order: {order_id}")
    
    async def refund_payment(
        self,
        payment_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Payment:
        """Refund a payment."""
        payment = await self.payment_repo.get(payment_id)
        if not payment:
            raise HTTPException(404, "Payment not found")
        
        # Check authorization (organizer of event or admin)
        order = await self.order_repo.get(payment.order_id)
        if order.event.organizer_id != user_id:
            # TODO: Check if user is admin
            raise HTTPException(403, "Not authorized")
        
        if payment.status != PaymentStatus.SUCCEEDED:
            raise HTTPException(400, "Cannot refund unsuccessful payment")
        
        try:
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                reason=reason or "requested_by_customer"
            )
            
            # Update payment status
            await self.payment_repo.update(
                payment_id,
                status=PaymentStatus.REFUNDED
            )
            
            # Update order status
            await self.order_repo.update(
                payment.order_id,
                status=OrderStatus.REFUNDED,
                payment_status=PaymentStatus.REFUNDED
            )
            
            logger.info(f"Refunded payment: {payment_id}")
            return await self.payment_repo.get(payment_id)
            
        except stripe.error.StripeError as e:
            logger.error(f"Refund failed: {str(e)}")
            raise HTTPException(400, f"Refund failed: {str(e)}")