"""Custom exception classes."""

from typing import Optional, Any


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None
    ):
        """Initialize exception.
        
        Args:
            message: Error message.
            status_code: HTTP status code.
            code: Error code for client.
            details: Additional error details.
        """
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        """Initialize not found exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=404,
            code="NOT_FOUND",
            details=details
        )


class UnauthorizedException(AppException):
    """Unauthorized access exception."""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        """Initialize unauthorized exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=401,
            code="UNAUTHORIZED",
            details=details
        )


class ForbiddenException(AppException):
    """Forbidden access exception."""
    
    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        """Initialize forbidden exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=403,
            code="FORBIDDEN",
            details=details
        )


class BadRequestException(AppException):
    """Bad request exception."""
    
    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        """Initialize bad request exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=400,
            code="BAD_REQUEST",
            details=details
        )


class ConflictException(AppException):
    """Resource conflict exception."""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        """Initialize conflict exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=409,
            code="CONFLICT",
            details=details
        )


class ValidationException(AppException):
    """Validation error exception."""
    
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        """Initialize validation exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=422,
            code="VALIDATION_ERROR",
            details=details
        )


class InsufficientStockException(AppException):
    """Insufficient ticket stock exception."""
    
    def __init__(self, message: str = "Insufficient stock", details: Optional[Any] = None):
        """Initialize insufficient stock exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=400,
            code="INSUFFICIENT_STOCK",
            details=details
        )


class PaymentException(AppException):
    """Payment processing exception."""
    
    def __init__(self, message: str = "Payment failed", details: Optional[Any] = None):
        """Initialize payment exception.
        
        Args:
            message: Error message.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            status_code=400,
            code="PAYMENT_ERROR",
            details=details
        )