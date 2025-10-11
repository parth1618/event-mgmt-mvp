"""Application constants and enums."""

from enum import Enum

# File upload constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
ALLOWED_DOCUMENT_MIMES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]


# Order statuses
class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


# Payment statuses
class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


# Event statuses
class EventStatus(str, Enum):
    """Event status enumeration."""

    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# User roles
class UserRole(str, Enum):
    """User role enumeration."""

    ATTENDEE = "attendee"
    ORGANIZER = "organizer"
    ADMIN = "admin"
    REVIEWER = "reviewer"  # For future RBAC


# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Token expiry
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Rate limiting
RATE_LIMIT_PER_MINUTE = 100
AUTH_RATE_LIMIT_PER_MINUTE = 20
