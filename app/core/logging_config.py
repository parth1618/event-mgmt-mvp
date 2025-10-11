"""Centralized logging configuration using Loguru with enhanced features."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import settings


def serialize_record(record: dict[str, Any]) -> dict[str, Any]:
    """Serialize log record for structured logging in production."""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add extra fields
    if record.get("extra"):
        subset["extra"] = record["extra"]

    # Add exception info if present
    if record.get("exception"):
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    return subset


def setup_logging() -> None:
    """Configure Loguru logger with appropriate handlers and formatting.

    This function should be called once during application startup.
    Configures different handlers based on environment (dev/prod).
    """
    # Remove default handler
    logger.remove()

    # Console handler with colored output (development)
    if settings.ENVIRONMENT == "development":
        logger.add(
            sys.stdout,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=settings.LOG_LEVEL,
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        # Production: JSON structured logging
        logger.add(
            sys.stdout,
            format="{message}",
            level=settings.LOG_LEVEL,
            serialize=True,
            backtrace=False,
            diagnose=False,
        )

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Application log file (all logs)
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        compression="zip",
        enqueue=True,  # Thread-safe async logging
    )

    # Error log file (errors and above)
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="90 days",
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message} | "
            "{extra}"
        ),
        backtrace=True,
        diagnose=True,
        compression="zip",
        enqueue=True,
    )

    # Access log for HTTP requests
    logger.add(
        log_dir / "access_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
        filter=lambda record: "http_request" in record["extra"],
        compression="zip",
        enqueue=True,
    )

    # Security log for authentication events
    logger.add(
        log_dir / "security_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="180 days",  # 6 months for security logs
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        filter=lambda record: "security_event" in record["extra"],
        compression="zip",
        enqueue=True,
    )

    logger.info(f"Logging configured for environment: {settings.ENVIRONMENT}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Log directory: {log_dir.absolute()}")


# Utility function for structured logging
def log_security_event(event_type: str, user_id: str = None, details: dict[str, Any] = None):
    """Log security-related events with structured data."""
    logger.bind(security_event=True).info(
        f"Security Event: {event_type}",
        extra={
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {},
        },
    )
