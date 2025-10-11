"""Email service with SendGrid integration option."""

from loguru import logger

from app.config import settings


class EmailService:
    """Service for sending emails via SendGrid or stub."""

    def __init__(self):
        """Initialize email service."""
        self.enabled = settings.EMAIL_ENABLED
        self.from_email = settings.FROM_EMAIL

        if self.enabled and settings.SENDGRID_API_KEY:
            try:
                import sendgrid

                self.sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
                logger.info("SendGrid email service initialized")
            except ImportError:
                logger.warning("SendGrid not installed, using stub")
                self.enabled = False
        else:
            self.enabled = False

    async def _send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send email via SendGrid or log stub.

        Args:
            to: Recipient email.
            subject: Email subject.
            html_content: HTML email body.
            text_content: Plain text email body.

        Returns:
            bool: True if sent successfully.
        """
        if not self.enabled:
            logger.info(
                f"[EMAIL STUB] To: {to}, Subject: {subject}\n"
                f"Content: {text_content or html_content[:100]}"
            )
            return True

        try:
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=self.from_email,
                to_emails=to,
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content,
            )

            response = self.sg.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to}: {subject}")
                return True
            else:
                logger.error(f"Email send failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

    async def send_welcome_email(self, to: str, name: str) -> bool:
        """Send welcome email to new user.

        Args:
            to: User email.
            name: User name.

        Returns:
            bool: Success status.
        """
        subject = f"Welcome to {settings.APP_NAME}!"

        html_content = f"""
        <html>
            <body>
                <h2>Welcome {name}!</h2>
                <p>Thank you for joining {settings.APP_NAME}.</p>
                <p>You can now start discovering and booking amazing events.</p>
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </body>
        </html>
        """

        text_content = f"Welcome {name}! Thank you for joining {settings.APP_NAME}."

        return await self._send_email(to, subject, html_content, text_content)

    async def send_order_confirmation(
        self, to: str, order_number: str, event_title: str, total_amount: float
    ) -> bool:
        """Send order confirmation email.

        Args:
            to: User email.
            order_number: Order number.
            event_title: Event title.
            total_amount: Total order amount.

        Returns:
            bool: Success status.
        """
        subject = f"Order Confirmation - {order_number}"

        html_content = f"""
        <html>
            <body>
                <h2>Order Confirmed!</h2>
                <p>Your order <strong>{order_number}</strong> has been confirmed.</p>
                <p><strong>Event:</strong> {event_title}</p>
                <p><strong>Total:</strong> ${total_amount:.2f}</p>
                <p>Your tickets will be available for download shortly.</p>
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </body>
        </html>
        """

        text_content = (
            f"Order Confirmed! Order: {order_number}, "
            f"Event: {event_title}, Total: ${total_amount:.2f}"
        )

        return await self._send_email(to, subject, html_content, text_content)

    async def send_ticket_email(self, to: str, order_number: str, pdf_url: str) -> bool:
        """Send email with ticket PDF link.

        Args:
            to: User email.
            order_number: Order number.
            pdf_url: Presigned URL for ticket PDF.

        Returns:
            bool: Success status.
        """
        subject = f"Your Tickets - {order_number}"

        html_content = f"""
        <html>
            <body>
                <h2>Your Tickets Are Ready!</h2>
                <p>Your tickets for order <strong>{order_number}</strong> are ready.</p>
                <p><a href="{pdf_url}">Download Your Tickets</a></p>
                <p>This link will expire in 7 days.</p>
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </body>
        </html>
        """

        text_content = f"Your tickets are ready! Download: {pdf_url}"

        return await self._send_email(to, subject, html_content, text_content)

    async def send_password_reset(self, to: str, reset_token: str) -> bool:
        """Send password reset email.

        Args:
            to: User email.
            reset_token: Password reset token.

        Returns:
            bool: Success status.
        """
        # In production, this would be a frontend URL
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"

        subject = "Password Reset Request"

        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested a password reset. Click the link below to reset your password:</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </body>
        </html>
        """

        text_content = f"Reset your password: {reset_url}"

        return await self._send_email(to, subject, html_content, text_content)

    async def send_event_reminder(self, to: str, event_title: str, start_datetime: str) -> bool:
        """Send event reminder email.

        Args:
            to: User email.
            event_title: Event title.
            start_datetime: Event start date/time.

        Returns:
            bool: Success status.
        """
        subject = f"Reminder: {event_title} is Tomorrow!"

        html_content = f"""
        <html>
            <body>
                <h2>Event Reminder</h2>
                <p>Don't forget! Your event is tomorrow:</p>
                <p><strong>{event_title}</strong></p>
                <p><strong>When:</strong> {start_datetime}</p>
                <p>Don't forget to bring your tickets!</p>
                <p>Best regards,<br>The {settings.APP_NAME} Team</p>
            </body>
        </html>
        """

        text_content = f"Reminder: {event_title} starts {start_datetime}"

        return await self._send_email(to, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
