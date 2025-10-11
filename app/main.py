"""FastAPI application entry point with complete production setup."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator  # noqa: UP035

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.v1.router import api_router
from app.config import settings
from app.core.cache import cache_manager
from app.core.exceptions import AppException
from app.core.logging_config import setup_logging
from app.core.middleware import (
    CompressionMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.database import close_db, init_db

# Configure Loguru logger
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown events.

    Handles:
    - Database initialization
    - Redis connection
    - Storage service setup
    - Graceful shutdown
    """
    # Startup
    logger.info("🚀 Starting Event Management MVP Backend")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Python version: {settings.VERSION}")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise

    # Initialize Redis cache
    try:
        await cache_manager.connect()
        if await cache_manager.ping():
            logger.info("✅ Redis cache connected successfully")
        else:
            logger.warning("⚠️ Redis connection check failed")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {str(e)}")
        logger.warning("Application will continue without caching")

    # Initialize storage service
    try:
        from app.services.storage_service import storage_service

        storage_service._ensure_bucket_exists()
        logger.info("✅ Storage service initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Storage service initialization failed: {str(e)}")

    # Log application URLs
    logger.info("🌐 Application URLs:")
    logger.info(f"  - API: http://localhost:{settings.PORT or 8000}")
    if settings.DEBUG:
        logger.info(f"  - Docs: http://localhost:{settings.PORT or 8000}/docs")
        logger.info(f"  - ReDoc: http://localhost:{settings.PORT or 8000}/redoc")

    logger.info("✅ Application startup complete")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Event Management MVP Backend")

    # Close database connections
    try:
        await close_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

    # Close Redis connection
    try:
        await cache_manager.disconnect()
        logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    logger.info("✅ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    Production-grade Event Management and Ticketing Platform API

    ## Features

    * **Authentication**: JWT-based with role management
    * **Events**: Full CRUD with search and filtering
    * **Tickets**: Multi-tier ticketing with inventory control
    * **Orders**: Transaction-safe order processing
    * **Payments**: Stripe integration with webhooks
    * **Background Tasks**: Celery for PDF generation and emails

    ## Rate Limits

    * General API: 100 requests/minute
    * Authentication: 10 requests/minute
    """,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hide schemas section by default
        "displayRequestDuration": True,
        "filter": True,
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add trusted host middleware (production)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.event-mgmt-mvp.com", "*.event-mgmt-mvp.com"],
    )

# Add custom middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CompressionMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    calls=settings.RATE_LIMIT_PER_MINUTE,
    period=60,
)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions.

    Args:
        request: FastAPI request object.
        exc: Application exception.

    Returns:
        JSONResponse: Error response.
    """
    logger.error(
        f"AppException: {exc.message}",
        extra={
            "code": exc.code,
            "details": exc.details,
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request object.
        exc: Validation error.

    Returns:
        JSONResponse: Error response.
    """
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={
            "errors": errors,
            "request_id": getattr(request.state, "request_id", None),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions.

    Args:
        request: FastAPI request object.
        exc: Exception.

    Returns:
        JSONResponse: Error response.
    """
    logger.error(
        f"Unexpected error on {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", None)},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": ("An unexpected error occurred" if not settings.DEBUG else str(exc)),
                "details": None,
            },
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# ============================================================================
# Routes
# ============================================================================

# Include API router
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"], include_in_schema=settings.DEBUG)
async def root() -> dict:
    """Root endpoint with API information.

    Returns:
        dict: Welcome message and API version.
    """
    return {
        "message": "Welcome to Event Management MVP API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "Contact admin for API documentation",
        "status": "operational",
    }


# Enhanced health check endpoint
@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> dict:
    """Comprehensive health check endpoint for monitoring.

    Returns:
        dict: Health status with component details.
    """
    from datetime import datetime

    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
    }

    # Check database
    try:
        from app.database import engine

        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_healthy = await cache_manager.ping()
        health_status["components"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
            "type": "redis",
        }
        if not redis_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check storage
    try:
        from app.services.storage_service import storage_service

        storage_service.client.list_buckets()
        health_status["components"]["storage"] = {
            "status": "healthy",
            "type": "minio/s3",
        }
    except Exception as e:
        health_status["components"]["storage"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    return health_status


# Readiness probe (Kubernetes/Docker)
@app.get("/ready", tags=["Health"], include_in_schema=False)
async def readiness_check() -> dict:
    """Readiness probe for container orchestration.

    Returns:
        dict: Readiness status.
    """
    try:
        from app.database import engine

        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"ready": True}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "message": "Database not ready"},
        )


# Liveness probe (Kubernetes/Docker)
@app.get("/live", tags=["Health"], include_in_schema=False)
async def liveness_check() -> dict:
    """Liveness probe for container orchestration.

    Returns:
        dict: Liveness status.
    """
    return {"alive": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT or 8000,
        reload=settings.DEBUG,
        log_config=None,  # Use loguru instead
        workers=1 if settings.DEBUG else 4,
        loop="uvloop",
        http="httptools",
    )
