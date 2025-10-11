"""Helper utility functions."""

import random
import string
from datetime import datetime
from uuid import UUID


def generate_order_number() -> str:
    """Generate unique order number.

    Returns:
        str: Order number in format ORD-YYYYMMDD-XXXXX
    """
    date_part = datetime.utcnow().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.digits, k=5))
    return f"ORD-{date_part}-{random_part}"


def generate_ticket_code(order_id: UUID, item_index: int) -> str:
    """Generate unique ticket code.

    Args:
        order_id: Order UUID.
        item_index: Index of ticket in order.

    Returns:
        str: Ticket code.
    """
    order_short = str(order_id)[:8].upper()
    return f"TKT-{order_short}-{item_index:03d}"


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string.

    Args:
        amount: Amount to format.
        currency: Currency code.

    Returns:
        str: Formatted currency string.
    """
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def slugify(text: str) -> str:
    """Convert text to URL-safe slug.

    Args:
        text: Text to slugify.

    Returns:
        str: Slugified text.
    """
    import re

    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def mask_email(email: str) -> str:
    """Mask email address for privacy.

    Args:
        email: Email address to mask.

    Returns:
        str: Masked email (e.g., j***@example.com)
    """
    if "@" not in email:
        return email

    local, domain = email.split("@")
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy.

    Args:
        phone: Phone number to mask.

    Returns:
        str: Masked phone (e.g., +1***-***-1234)
    """
    if not phone or len(phone) < 4:
        return phone

    return phone[:2] + "*" * (len(phone) - 6) + phone[-4:]


def calculate_pagination(total: int, page: int, page_size: int) -> dict:
    """Calculate pagination metadata.

    Args:
        total: Total number of items.
        page: Current page number (1-indexed).
        page_size: Items per page.

    Returns:
        dict: Pagination metadata.
    """
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }


def validate_date_range(start: datetime, end: datetime) -> bool:
    """Validate that end date is after start date.

    Args:
        start: Start datetime.
        end: End datetime.

    Returns:
        bool: True if valid, False otherwise.
    """
    return end > start
