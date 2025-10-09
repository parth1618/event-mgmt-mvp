"""Background tasks for ticket generation and notifications."""

from celery import shared_task
from loguru import logger
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
import uuid
from typing import List, Dict

@shared_task(bind=True, max_retries=3)
def send_email_stub(self, to: str, subject: str, body: str):
    """Stub for sending email (logs instead).
    
    Args:
        to: Recipient email.
        subject: Email subject.
        body: Email body.
        
    Returns:
        bool: Success status.
    """
    try:
        logger.info(f"[EMAIL STUB] To: {to}, Subject: {subject}")
        logger.debug(f"[EMAIL STUB] Body: {body}")
        return True
    except Exception as exc:
        logger.error(f"Email task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_ticket_pdf(self, order_id: str):
    """Generate PDF tickets with QR codes.
    
    Args:
        order_id: Order UUID string.
        
    Returns:
        str: S3 key of generated PDF.
    """
    try:
        from app.database import async_session_maker
        from app.repositories.order import OrderRepository
        from app.services.storage_service import storage_service
        from uuid import UUID
        import asyncio
        
        async def _generate():
            async with async_session_maker() as session:
                # Get order with items
                order_repo = OrderRepository(session)
                order = await order_repo.get_with_items(UUID(order_id))
                
                if not order:
                    raise ValueError(f"Order not found: {order_id}")
                
                # Generate PDF
                buffer = BytesIO()
                pdf = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter
                
                # Add header
                pdf.setFont("Helvetica-Bold", 24)
                pdf.drawString(1*inch, height - 1*inch, "Event Tickets")
                
                pdf.setFont("Helvetica", 12)
                pdf.drawString(1*inch, height - 1.5*inch, f"Order: {order.order_number}")
                pdf.drawString(1*inch, height - 1.8*inch, f"Event: {order.event.title}")
                pdf.drawString(1*inch, height - 2.1*inch, f"Date: {order.event.start_datetime.strftime('%B %d, %Y at %I:%M %p')}")
                pdf.drawString(1*inch, height - 2.4*inch, f"Location: {order.event.location}")
                
                # Generate ticket for each item
                y_position = height - 3.5*inch
                
                for item in order.items:
                    ticket = item.ticket
                    
                    for i in range(item.quantity):
                        if y_position < 2*inch:
                            pdf.showPage()
                            y_position = height - 1*inch
                        
                        # Draw ticket box
                        pdf.rect(0.5*inch, y_position - 1.5*inch, 7*inch, 1.8*inch, stroke=1, fill=0)
                        
                        # Ticket details
                        pdf.setFont("Helvetica-Bold", 14)
                        pdf.drawString(0.75*inch, y_position - 0.3*inch, f"{ticket.name}")
                        
                        pdf.setFont("Helvetica", 10)
                        pdf.drawString(0.75*inch, y_position - 0.6*inch, f"Ticket #{i+1} of {item.quantity}")
                        pdf.drawString(0.75*inch, y_position - 0.9*inch, f"Price: ${item.unit_price:.2f}")
                        
                        # Generate QR code
                        qr_data = f"{order.order_number}:{order_id}:{ticket.id}:{i+1}"
                        qr = qrcode.QRCode(version=1, box_size=10, border=2)
                        qr.add_data(qr_data)
                        qr.make(fit=True)
                        
                        qr_img = qr.make_image(fill_color="black", back_color="white")
                        qr_buffer = BytesIO()
                        qr_img.save(qr_buffer, format='PNG')
                        qr_buffer.seek(0)
                        
                        # Draw QR code
                        pdf.drawImage(
                            qr_buffer,
                            6*inch,
                            y_position - 1.3*inch,
                            width=1.2*inch,
                            height=1.2*inch
                        )
                        
                        y_position -= 2.2*inch
                
                # Finalize PDF
                pdf.save()
                buffer.seek(0)
                
                # Upload to storage
                filename = f"tickets/{order_id}.pdf"
                storage_service.client.put_object(
                    Bucket=storage_service.bucket,
                    Key=filename,
                    Body=buffer.getvalue(),
                    ContentType='application/pdf'
                )
                
                logger.info(f"Generated ticket PDF for order: {order_id}")
                
                # Send email with download link
                from app.services.email_service import email_service
                url = storage_service.get_presigned_url(filename, expiration=7*24*3600)  # 7 days
                await email_service.send_ticket_email(
                    to=order.user.email,
                    order_number=order.order_number,
                    pdf_url=url
                )
                
                return filename
        
        # Run async function
        return asyncio.run(_generate())
        
    except Exception as exc:
        logger.error(f"Ticket generation failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


@shared_task
def send_event_reminders():
    """Send reminders for upcoming events (scheduled task).
    
    Should be run daily to check for events starting in 24 hours.
    """
    try:
        from app.database import async_session_maker
        from app.repositories.order import OrderRepository
        from app.services.email_service import email_service
        from datetime import datetime, timedelta
        import asyncio
        
        async def _send_reminders():
            async with async_session_maker() as session:
                # Get events starting in 24 hours
                tomorrow = datetime.utcnow() + timedelta(days=1)
                start_window = tomorrow.replace(hour=0, minute=0, second=0)
                end_window = tomorrow.replace(hour=23, minute=59, second=59)
                
                # Query orders for events in window
                from sqlalchemy import select, and_
                from app.models.order import Order
                from app.models.event import Event
                from app.utils.constants import OrderStatus, PaymentStatus
                
                result = await session.execute(
                    select(Order)
                    .join(Event)
                    .where(
                        and_(
                            Event.start_datetime >= start_window,
                            Event.start_datetime <= end_window,
                            Order.status == OrderStatus.CONFIRMED,
                            Order.payment_status == PaymentStatus.SUCCEEDED
                        )
                    )
                )
                orders = result.scalars().all()
                
                # Send reminder for each order
                for order in orders:
                    await email_service.send_event_reminder(
                        to=order.user.email,
                        event_title=order.event.title,
                        start_datetime=order.event.start_datetime.strftime('%B %d, %Y at %I:%M %p')
                    )
                
                logger.info(f"Sent {len(orders)} event reminders")
        
        asyncio.run(_send_reminders())
        
    except Exception as exc:
        logger.error(f"Event reminder task failed: {exc}")
