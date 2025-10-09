"""Constants and enums used throughout the application."""

from enum import Enum


class UserRole(str, Enum):
    """User roles for role-based access control."""
    
    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    ADMIN = "admin"


class EventStatus(str, Enum):
    """Event publication status."""
    
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class OrderStatus(str, Enum):
    """Order processing status."""
    
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment transaction status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


# File upload constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache TTL
CACHE_TTL_EVENT_LIST = 300  # 5 minutes
CACHE_TTL_EVENT_DETAIL = 600  # 10 minutes