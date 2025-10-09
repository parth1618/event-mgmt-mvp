"""Helper utility functions."""

import uuid
import random
import string
import re
from datetime import datetime
from typing import Optional
import qrcode
from io import BytesIO


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4.
    
    Returns:
        uuid.UUID: New UUID.
    """
    return uuid.uuid4()


def generate_order_number() -> str:
    """Generate a unique order number.
    
    Returns:
        str: Order number in format EVT-YYYYMMDD-XXXXX.
        
    Example:
        >>> generate_order_number()
        'EVT-20241215-A3K9Z'
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"EVT-{date_str}-{random_str}"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.
    
    Args:
        text: Text to convert.
        
    Returns:
        str: Slugified text.
        
    Example:
        >>> slugify("My Awesome Event 2024!")
        'my-awesome-event-2024'
    """
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def generate_qr_code(data: str) -> BytesIO:
    """Generate QR code image.
    
    Args:
        data: Data to encode in QR code.
        
    Returns:
        BytesIO: QR code image as bytes.
        
    Example:
        >>> qr_bytes = generate_qr_code("https://event.com/ticket/123")
        >>> # Upload qr_bytes to storage
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string.
    
    Args:
        amount: Amount to format.
        currency: Currency code.
        
    Returns:
        str: Formatted currency string.
        
    Example:
        >>> format_currency(1234.56)
        '$1,234.56'
    """
    if currency.upper() == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def calculate_pagination(
    total: int,
    page: int,
    size: int
) -> dict:
    """Calculate pagination metadata.
    
    Args:
        total: Total number of items.
        page: Current page number (1-indexed).
        size: Items per page.
        
    Returns:
        dict: Pagination metadata.
        
    Example:
        >>> calculate_pagination(total=100, page=2, size=20)
        {'total': 100, 'page': 2, 'size': 20, 'pages': 5}
    """
    pages = (total + size - 1) // size  # Ceiling division
    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }