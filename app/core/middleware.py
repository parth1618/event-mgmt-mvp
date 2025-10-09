"""Custom middleware for logging and rate limiting."""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests and responses."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request and log details.
        
        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.
            
        Returns:
            Response: Response from handler.
        """
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} - {duration:.3f}s",
                extra={
                    "status_code": response.status_code,
                    "duration": duration,
                    "path": request.url.path,
                }
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)} - {duration:.3f}s",
                extra={
                    "error": str(e),
                    "duration": duration,
                    "path": request.url.path,
                },
                exc_info=True
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting (basic implementation).
    
    Note: In production, use SlowAPI or similar Redis-backed solution.
    """
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with rate limiting.
        
        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.
            
        Returns:
            Response: Response from handler.
        """
        # Rate limiting is handled by SlowAPI in main.py
        # This is a placeholder for custom rate limit logic if needed
        response = await call_next(request)
        return response