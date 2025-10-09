"""Email service (stubbed for MVP)."""

from loguru import logger
from typing import Optional

class EmailService:
    """Service for sending emails (stubbed)."""
    
    @staticmethod
    async def send_welcome_email(to: str, name: str) -> bool:
        """Send welcome email to new user."""
        logger.info(f"[EMAIL STUB] Welcome email to: {to}, name: {name}")
        return True
    
    @staticmethod
    async def send_order_confirmation(
        to: str,
        order_number: str,
        event_title: str,
        total_amount: float
    ) -> bool:
        """Send order confirmation email."""
        logger.info(
            f"[EMAIL STUB] Order confirmation to: {to}, "
            f"order: {order_number}, event: {event_title}, amount: ${total_amount}"
        )
        return True
    
    @staticmethod
    async def send_ticket_email(to: str, order_number: str, pdf_url: str) -> bool:
        """Send email with ticket PDF."""
        logger.info(
            f"[EMAIL STUB] Ticket email to: {to}, "
            f"order: {order_number}, PDF: {pdf_url}"
        )
        return True
    
    @staticmethod
    async def send_password_reset(to: str, reset_token: str) -> bool:
        """Send password reset email."""
        logger.info(f"[EMAIL STUB] Password reset to: {to}, token: {reset_token}")
        return True
    
    @staticmethod
    async def send_event_reminder(
        to: str,
        event_title: str,
        start_datetime: str
    ) -> bool:
        """Send event reminder email."""
        logger.info(
            f"[EMAIL STUB] Event reminder to: {to}, "
            f"event: {event_title}, starts: {start_datetime}"
        )
        return True

email_service = EmailService()