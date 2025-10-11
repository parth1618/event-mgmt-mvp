"""Stripe payment integration service."""

import hashlib
import hmac
import json
import time
from uuid import UUID

import stripe
from fastapi import HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import Payment
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.utils.constants import OrderStatus, PaymentStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    """Service for handling Stripe payments."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.payment_repo = PaymentRepository(db)

    async def create_payment_intent(self, order_id: UUID, user_id: UUID) -> Payment:
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
                idempotency_key=f"order_{order_id}",
            )

            # Create payment record
            payment = await self.payment_repo.create(
                order_id=order_id,
                stripe_payment_intent_id=intent.id,
                amount=order.total_amount,
                currency="usd",
                status=PaymentStatus.PENDING,
            )

            logger.info(f"Created payment intent: {intent.id} for order: {order_id}")
            return payment

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(400, f"Payment creation failed: {str(e)}")

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Handle Stripe webhook events with signature verification."""
        try:
            # Get timestamp and signature from header
            # Format: t=timestamp,v1=signature
            if not sig_header:
                raise ValueError("Missing Stripe signature header")

            timestamp_str = None
            signature = None

            for item in sig_header.split(","):
                key, value = item.split("=", 1)
                if key == "t":
                    timestamp_str = value
                elif key == "v1":
                    signature = value

            if not timestamp_str or not signature:
                raise ValueError("Invalid signature format")

            timestamp = int(timestamp_str)

            # Verify timestamp is within 5 minute window (prevent replay attacks)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                raise ValueError("Webhook timestamp outside tolerance window")

            # Verify HMAC signature
            signed_content = f"{timestamp_str}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                settings.STRIPE_WEBHOOK_SECRET.encode(),
                signed_content.encode(),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_sig):
                raise ValueError("Invalid webhook signature")

            # Parse event
            event = json.loads(payload)

        except ValueError as e:
            logger.error(f"Webhook validation failed: {str(e)}")
            raise HTTPException(400, f"Invalid webhook: {str(e)}")
        except Exception as e:
            logger.error(f"Webhook parsing error: {str(e)}")
            raise HTTPException(400, "Invalid webhook payload")

        # Handle event types
        if event["type"] == "payment_intent.succeeded":
            await self._handle_payment_succeeded(event["data"]["object"])
        elif event["type"] == "payment_intent.payment_failed":
            await self._handle_payment_failed(event["data"]["object"])

        return {"status": "success"}

    async def _handle_payment_succeeded(self, payment_intent: dict) -> None:
        """Handle successful payment."""
        intent_id = payment_intent["id"]
        order_id = payment_intent["metadata"].get("order_id")

        if not order_id:
            logger.error(f"No order_id in payment intent: {intent_id}")
            return

        payment = await self.payment_repo.get_by_stripe_id(intent_id)
        if payment:
            await self.payment_repo.update(payment.id, status=PaymentStatus.SUCCEEDED)  # ✓ CORRECT
            await self.order_repo.update(
                UUID(order_id),
                status=OrderStatus.CONFIRMED,
                payment_status=PaymentStatus.SUCCEEDED,
            )
            logger.info(f"Payment succeeded for order: {order_id}")

            # Trigger background task for ticket generation
            from app.tasks.tasks import generate_ticket_pdf

            generate_ticket_pdf.delay(str(UUID(order_id)))

    async def refund_payment(
        self, payment_id: UUID, user_id: UUID, reason: str | None = None
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
            stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                reason=reason or "requested_by_customer",
            )

            # Update payment status
            await self.payment_repo.update(payment_id, status=PaymentStatus.REFUNDED)

            # Update order status
            await self.order_repo.update(
                payment.order_id,
                status=OrderStatus.REFUNDED,
                payment_status=PaymentStatus.REFUNDED,
            )

            logger.info(f"Refunded payment: {payment_id}")
            return await self.payment_repo.get(payment_id)

        except stripe.error.StripeError as e:
            logger.error(f"Refund failed: {str(e)}")
            raise HTTPException(400, f"Refund failed: {str(e)}")
