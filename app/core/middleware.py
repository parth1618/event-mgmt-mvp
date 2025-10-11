"""Production-grade middleware for logging, rate limiting, and security."""

import time
from typing import Callable  # noqa: UP035
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache_manager
from app.core.logging_config import log_security_event


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced middleware for comprehensive request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with detailed logging and metrics.

        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.

        Returns:
            Response: Response from handler.
        """
        # Generate unique request ID
        request_id = str(uuid4())
        request.state.request_id = request_id

        # Extract request details
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        start_time = time.time()

        # Log incoming request
        logger.bind(http_request=True).info(
            f"→ {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration:.3f}s"

            # Log response
            log_level = "WARNING" if response.status_code >= 400 else "INFO"
            logger.bind(http_request=True).log(
                log_level,
                f"← {response.status_code} {request.method} {request.url.path} - {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                    "path": request.url.path,
                    "method": request.method,
                },
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ Request failed: {str(e)} - {duration:.3f}s",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": duration,
                    "path": request.url.path,
                    "method": request.method,
                },
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed rate limiting middleware with sliding window."""

    def __init__(self, app, calls: int = 100, period: int = 60):
        """Initialize rate limiter.

        Args:
            app: FastAPI application.
            calls: Number of calls allowed.
            period: Time period in seconds.
        """
        super().__init__(app)
        self.calls = calls
        self.period = period

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.

        Returns:
            Response: Response from handler.
        """
        # Skip rate limiting for health checks
        if request.url.path in [
            "/api/v1/health",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]:
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Create rate limit key
        rate_key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            # Check current count
            current = await cache_manager.get(rate_key)

            if current is None:
                # First request, set counter
                await cache_manager.set(rate_key, 1, self.period)
            elif current >= self.calls:
                # Rate limit exceeded
                log_security_event(
                    "rate_limit_exceeded",
                    details={
                        "client_ip": client_ip,
                        "path": request.url.path,
                        "limit": self.calls,
                    },
                )

                from fastapi import HTTPException

                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {self.period} seconds.",
                    headers={
                        "X-RateLimit-Limit": str(self.calls),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + self.period)),
                    },
                )
            else:
                # Increment counter
                await cache_manager.increment(rate_key)

        except Exception as e:
            # If Redis fails, allow request through but log error
            logger.warning(f"Rate limiting check failed: {e}")

        response = await call_next(request)

        # Add rate limit headers
        try:
            current = await cache_manager.get(rate_key) or 0
            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - current))
        except Exception:
            pass

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add comprehensive security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.

        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.

        Returns:
            Response: Response with security headers.
        """
        response = await call_next(request)

        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": "default-src 'self'",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware for response compression."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add compression hint to response.

        Args:
            request: Incoming request.
            call_next: Next middleware/route handler.

        Returns:
            Response: Response with compression headers.
        """
        response = await call_next(request)

        # Add Vary header for caching
        response.headers["Vary"] = "Accept-Encoding"

        return response
