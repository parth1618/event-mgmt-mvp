"""Payment processing endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_organizer, get_current_user
from app.schemas.payment import PaymentIntentCreate, PaymentOut, PaymentRefund
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/create-intent", response_model=PaymentOut, status_code=201)
async def create_payment_intent(
    intent_data: PaymentIntentCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe payment intent.

    Creates a Stripe PaymentIntent for the specified order.
    Returns client_secret to complete payment on frontend.

    **Requires**: Authenticated user who owns the order.
    """
    service = PaymentService(db)
    return await service.create_payment_intent(intent_data.order_id, current_user.id)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events.

    **Webhook Events Handled**:
    - `payment_intent.succeeded`: Confirms order, generates tickets
    - `payment_intent.payment_failed`: Marks payment as failed

    **Note**: This endpoint must be registered in Stripe Dashboard.
    """
    service = PaymentService(db)
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    return await service.handle_webhook(payload, sig_header)


@router.post("/{payment_id}/refund", response_model=PaymentOut)
async def refund_payment(
    payment_id: UUID,
    refund_data: PaymentRefund,
    current_user=Depends(get_current_organizer),
    db: AsyncSession = Depends(get_db),
):
    """Refund payment.

    Creates a Stripe refund and updates order status.

    **Requires**: Organizer role and ownership of event.
    **Note**: Only successful payments can be refunded.
    """
    service = PaymentService(db)
    return await service.refund_payment(payment_id, current_user.id, refund_data.reason)


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment details.

    **Requires**: Authenticated user who owns the associated order.
    """
    from fastapi import HTTPException

    from app.repositories.payment import PaymentRepository

    payment_repo = PaymentRepository(db)
    payment = await payment_repo.get(payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    # Check authorization
    from app.repositories.order import OrderRepository

    order = await OrderRepository(db).get(payment.order_id)
    if order.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")

    return payment
