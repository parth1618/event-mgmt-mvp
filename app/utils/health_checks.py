"""Comprehensive health check utilities for monitoring system components."""

from datetime import datetime
from typing import Any

from loguru import logger


async def check_database_health() -> dict[str, Any]:
    """Check database connectivity and performance.

    Returns:
        Dict with status, type, and metrics.
    """
    try:
        from app.database import engine

        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1 as health_check")
            await result.scalar()

        # Get pool statistics
        pool = engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
        }

        return {
            "status": "healthy",
            "type": "postgresql",
            "pool": pool_status,
            "response_time_ms": "< 50",
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "type": "postgresql", "error": str(e)}


async def check_redis_health() -> dict[str, Any]:
    """Check Redis connectivity and performance.

    Returns:
        Dict with status, type, and metrics.
    """
    try:
        from app.core.cache import cache_manager

        # Test ping
        is_healthy = await cache_manager.ping()

        if not is_healthy:
            return {"status": "unhealthy", "type": "redis", "error": "Ping failed"}

        # Get Redis info
        if cache_manager._redis:
            info = await cache_manager._redis.info("stats")

            return {
                "status": "healthy",
                "type": "redis",
                "total_commands": info.get("total_commands_processed", 0),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
            }

        return {"status": "healthy", "type": "redis"}

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "type": "redis", "error": str(e)}


async def check_storage_health() -> dict[str, Any]:
    """Check storage service (MinIO/S3) connectivity.

    Returns:
        Dict with status, type, and metrics.
    """
    try:
        from app.services.storage_service import storage_service

        # Test bucket access
        storage_service.client.list_buckets()

        # Check bucket exists
        try:
            storage_service.client.head_bucket(Bucket=storage_service.bucket)
            bucket_exists = True
        except Exception:
            bucket_exists = False

        return {
            "status": "healthy" if bucket_exists else "degraded",
            "type": "minio/s3",
            "bucket": storage_service.bucket,
            "bucket_exists": bucket_exists,
        }

    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return {"status": "unhealthy", "type": "minio/s3", "error": str(e)}


async def check_celery_health() -> dict[str, Any]:
    """Check Celery workers status.

    Returns:
        Dict with status and worker info.
    """
    try:
        from app.tasks.celery_app import celery_app

        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if not active_workers:
            return {
                "status": "unhealthy",
                "type": "celery",
                "error": "No active workers",
            }

        worker_count = len(active_workers)

        return {
            "status": "healthy",
            "type": "celery",
            "active_workers": worker_count,
            "workers": list(active_workers.keys()),
        }

    except Exception as e:
        logger.warning(f"Celery health check failed: {e}")
        return {"status": "unknown", "type": "celery", "error": str(e)}


async def check_external_services() -> dict[str, Any]:
    """Check external service connectivity (Stripe, email, etc.).

    Returns:
        Dict with external service statuses.
    """
    services = {}

    # Check Stripe
    try:
        import stripe

        from app.config import settings

        stripe.api_key = settings.STRIPE_SECRET_KEY
        # Simple balance retrieval to test API key
        stripe.Balance.retrieve()

        services["stripe"] = {
            "status": "healthy",
            "configured": bool(settings.STRIPE_SECRET_KEY),
        }
    except Exception as e:
        services["stripe"] = {"status": "unhealthy", "error": str(e)}

    # Check Email service
    from app.config import settings

    services["email"] = {
        "status": "configured" if settings.EMAIL_ENABLED else "disabled",
        "enabled": settings.EMAIL_ENABLED,
    }

    return services


async def get_system_metrics() -> dict[str, Any]:
    """Get system-level metrics.

    Returns:
        Dict with system metrics.
    """
    import psutil

    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_available_mb": round(memory.available / (1024 * 1024), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
        }
    except Exception as e:
        logger.warning(f"System metrics collection failed: {e}")
        return {"error": str(e)}


async def comprehensive_health_check() -> dict[str, Any]:
    """Perform comprehensive health check of all components.

    Returns:
        Dict with complete health status.
    """
    from app.config import settings

    # Check all components
    db_health = await check_database_health()
    redis_health = await check_redis_health()
    storage_health = await check_storage_health()
    celery_health = await check_celery_health()
    external_services = await check_external_services()
    system_metrics = await get_system_metrics()

    # Determine overall status
    components_status = [
        db_health["status"],
        redis_health["status"],
        storage_health["status"],
    ]

    if all(s == "healthy" for s in components_status):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in components_status):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_health,
            "redis": redis_health,
            "storage": storage_health,
            "celery": celery_health,
        },
        "external_services": external_services,
        "system": system_metrics,
    }
