"""Common schemas used across the application."""

from typing import Any, Optional, List, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""
    
    success: bool = True
    data: T
    message: str = "Success"


class ErrorDetail(BaseModel):
    """Error detail schema."""
    
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""
    
    success: bool = False
    error: ErrorDetail


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    total: int
    page: int
    size: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    success: bool = True
    data: List[T]
    pagination: PaginationMeta
    message: str = "Success"


class HealthCheck(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str