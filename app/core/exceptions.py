"""Custom exception classes for the application.

This module defines all custom exceptions used throughout the application
for consistent error handling and reporting.
"""

from typing import Any


class AppException(Exception):
    """Base exception class for all application exceptions.

    Attributes:
        message: Human-readable error message.
        code: Error code for client identification.
        status_code: HTTP status code.
        details: Additional error details.
    """

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        """Initialize application exception.

        Args:
            message: Error message.
            code: Error code identifier.
            status_code: HTTP status code.
            details: Additional error context.
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response.

        Returns:
            Dictionary representation of the exception.
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class InsufficientStockException(AppException):
    """Exception raised when attempting to order more items than available.

    Used in order processing when ticket inventory is insufficient.
    """

    def __init__(
        self,
        message: str = "Insufficient stock available",
        ticket_id: str | None = None,
        requested: int | None = None,
        available: int | None = None,
    ):
        """Initialize insufficient stock exception.

        Args:
            message: Error message.
            ticket_id: ID of the ticket with insufficient stock.
            requested: Quantity requested.
            available: Quantity available.
        """
        details = {}
        if ticket_id:
            details["ticket_id"] = ticket_id
        if requested is not None:
            details["requested"] = requested
        if available is not None:
            details["available"] = available

        super().__init__(
            message=message,
            code="INSUFFICIENT_STOCK",
            status_code=400,
            details=details,
        )


class AuthenticationException(AppException):
    """Exception raised for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication exception.

        Args:
            message: Error message.
        """
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=401,
        )


class AuthorizationException(AppException):
    """Exception raised for authorization failures."""

    def __init__(self, message: str = "Insufficient permissions"):
        """Initialize authorization exception.

        Args:
            message: Error message.
        """
        super().__init__(
            message=message,
            code="AUTHORIZATION_FAILED",
            status_code=403,
        )


class ResourceNotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):
        """Initialize resource not found exception.

        Args:
            message: Error message.
            resource_type: Type of resource (e.g., 'Event', 'User').
            resource_id: ID of the resource.
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ValidationException(AppException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: dict[str, str] | None = None,
    ):
        """Initialize validation exception.

        Args:
            message: Error message.
            field_errors: Dictionary of field-specific errors.
        """
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"field_errors": field_errors or {}},
        )


class PaymentException(AppException):
    """Exception raised for payment processing errors."""

    def __init__(
        self,
        message: str = "Payment processing failed",
        payment_provider: str = "stripe",
        provider_error: str | None = None,
    ):
        """Initialize payment exception.

        Args:
            message: Error message.
            payment_provider: Payment provider name.
            provider_error: Error from payment provider.
        """
        details = {"payment_provider": payment_provider}
        if provider_error:
            details["provider_error"] = provider_error

        super().__init__(
            message=message,
            code="PAYMENT_ERROR",
            status_code=402,
            details=details,
        )


class RateLimitException(AppException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        """Initialize rate limit exception.

        Args:
            message: Error message.
            retry_after: Seconds until retry is allowed.
        """
        details = {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class StorageException(AppException):
    """Exception raised for file storage errors."""

    def __init__(
        self,
        message: str = "Storage operation failed",
        operation: str | None = None,
    ):
        """Initialize storage exception.

        Args:
            message: Error message.
            operation: Storage operation that failed (upload, delete, etc.).
        """
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            code="STORAGE_ERROR",
            status_code=500,
            details=details,
        )


class EventNotFoundException(ResourceNotFoundException):
    """Exception raised when an event is not found."""

    def __init__(self, event_id: str):
        """Initialize event not found exception.

        Args:
            event_id: ID of the event.
        """
        super().__init__(
            message=f"Event {event_id} not found",
            resource_type="Event",
            resource_id=event_id,
        )


class OrderNotFoundException(ResourceNotFoundException):
    """Exception raised when an order is not found."""

    def __init__(self, order_id: str):
        """Initialize order not found exception.

        Args:
            order_id: ID of the order.
        """
        super().__init__(
            message=f"Order {order_id} not found",
            resource_type="Order",
            resource_id=order_id,
        )


class TicketNotFoundException(ResourceNotFoundException):
    """Exception raised when a ticket is not found."""

    def __init__(self, ticket_id: str):
        """Initialize ticket not found exception.

        Args:
            ticket_id: ID of the ticket.
        """
        super().__init__(
            message=f"Ticket {ticket_id} not found",
            resource_type="Ticket",
            resource_id=ticket_id,
        )
