"""Payment repository."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from app.models.payment import Payment
from app.repositories.base import BaseRepository

class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment model."""
    
    def __init__(self, db):
        super().__init__(Payment, db)
    
    async def get_by_stripe_id(self, stripe_id: str) -> Optional[Payment]:
        """Get payment by Stripe payment intent ID.
        
        Args:
            stripe_id: Stripe payment intent ID.
            
        Returns:
            Optional[Payment]: Payment if found.
        """
        result = await self.db.execute(
            select(Payment)
            .where(Payment.stripe_payment_intent_id == stripe_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_order(self, order_id: UUID) -> Optional[Payment]:
        """Get payment by order ID.
        
        Args:
            order_id: Order UUID.
            
        Returns:
            Optional[Payment]: Payment if found.
        """
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()