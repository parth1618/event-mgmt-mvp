"""Application configuration using Pydantic settings with comprehensive validation."""

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration is loaded from .env file or environment variables.
    Validates required fields and provides defaults where appropriate.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_NAME: str = "Event Management MVP"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production")
    LOG_LEVEL: str = Field(default="INFO")
    PORT: int = Field(default=8000, ge=1024, le=65535)

    # ========================================================================
    # Database Configuration
    # ========================================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://eventbrite:eventbrite123@localhost:5432/eventbrite_mvp"
    )
    DB_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DB_MAX_OVERFLOW: int = Field(default=40, ge=10, le=100)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5, le=60)
    DB_POOL_RECYCLE: int = Field(default=3600, ge=300)
    DB_ECHO: bool = Field(default=False)

    # ========================================================================
    # Security Configuration
    # ========================================================================
    SECRET_KEY: str = Field(default="", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440, ge=15, le=10080)  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # Password Requirements
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=8, le=128)
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False

    # ========================================================================
    # Stripe Payment Configuration
    # ========================================================================
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_PUBLISHABLE_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    STRIPE_API_VERSION: str = "2023-10-16"

    # ========================================================================
    # Redis Configuration
    # ========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=10, le=200)
    CACHE_TTL_SECONDS: int = Field(default=300, ge=60, le=3600)  # 5 minutes
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, ge=1, le=30)
    REDIS_SOCKET_KEEPALIVE: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(default=30, ge=10, le=120)

    # ========================================================================
    # Celery Configuration
    # ========================================================================
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_TASK_TIME_LIMIT: int = Field(default=1800, ge=60, le=3600)  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=1500, ge=60, le=3000)  # 25 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = Field(default=4, ge=1, le=10)
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(default=1000, ge=100, le=10000)

    # ========================================================================
    # MinIO/S3 Storage Configuration
    # ========================================================================
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "eventslake-bucket"
    MINIO_SECURE: bool = False
    MINIO_REGION: str = "us-east-1"

    # AWS S3 (alternative to MinIO)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_S3_REGION: str = "us-east-1"
    USE_S3: bool = False  # If True, use S3 instead of MinIO

    # ========================================================================
    # CORS Configuration
    # ========================================================================
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins."""
        if isinstance(v, list):
            return v
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # ========================================================================
    # Rate Limiting Configuration
    # ========================================================================
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, ge=10, le=1000)
    AUTH_RATE_LIMIT_PER_MINUTE: int = Field(default=10, ge=5, le=50)
    RATE_LIMIT_ENABLED: bool = True

    # ========================================================================
    # File Upload Configuration
    # ========================================================================
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp,image/gif"
    ALLOWED_DOCUMENT_TYPES: str = "application/pdf"

    @field_validator("ALLOWED_IMAGE_TYPES", "ALLOWED_DOCUMENT_TYPES")
    @classmethod
    def parse_allowed_types(cls, v: str) -> list[str]:
        """Parse comma-separated MIME types."""
        if isinstance(v, list):
            return v
        return [t.strip() for t in v.split(",") if t.strip()]

    # ========================================================================
    # Email Configuration
    # ========================================================================
    FROM_EMAIL: str = "noreply@event-mgmt-mvp.com"
    FROM_NAME: str = "Event Management MVP"
    SENDGRID_API_KEY: str = Field(default="")
    EMAIL_ENABLED: bool = Field(default=False)

    # SMTP (alternative to SendGrid)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = True
    USE_SMTP: bool = False

    # ========================================================================
    # Pagination Configuration
    # ========================================================================
    DEFAULT_PAGE_SIZE: int = Field(default=20, ge=1, le=100)
    MAX_PAGE_SIZE: int = Field(default=100, ge=10, le=500)

    # ========================================================================
    # Monitoring & Observability
    # ========================================================================
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str | None = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)

    # Metrics
    PROMETHEUS_ENABLED: bool = False
    METRICS_PORT: int = Field(default=9090, ge=1024, le=65535)

    # ========================================================================
    # Feature Flags
    # ========================================================================
    FEATURE_WEBSOCKETS: bool = False
    FEATURE_ANALYTICS: bool = False
    FEATURE_RECOMMENDATIONS: bool = False
    FEATURE_SOCIAL_LOGIN: bool = False

    # ========================================================================
    # Business Logic Configuration
    # ========================================================================
    ORDER_EXPIRY_MINUTES: int = Field(default=30, ge=5, le=120)
    TICKET_RESERVATION_MINUTES: int = Field(default=10, ge=1, le=30)
    MAX_TICKETS_PER_ORDER: int = Field(default=20, ge=1, le=100)
    REFUND_WINDOW_DAYS: int = Field(default=7, ge=1, le=30)

    # ========================================================================
    # Validators
    # ========================================================================

    @model_validator(mode="after")
    def validate_environment_specific(self):
        """Validate environment-specific settings."""
        if self.ENVIRONMENT == "production":
            # Production security checks
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")

            if "localhost" in self.DATABASE_URL.lower():
                raise ValueError("Production DATABASE_URL cannot use localhost")

            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")

            if self.SECRET_KEY == "dev-secret-key-change-in-production-min-32-chars":
                raise ValueError("Must change SECRET_KEY from default value in production")

            # Stripe validation
            if not self.STRIPE_SECRET_KEY or self.STRIPE_SECRET_KEY.startswith("sk_test"):
                raise ValueError("Must use live Stripe keys in production")

            # Rate limiting should be enabled
            if not self.RATE_LIMIT_ENABLED:
                raise ValueError("Rate limiting must be enabled in production")

        # Development warnings
        if self.ENVIRONMENT == "development":
            if len(self.SECRET_KEY) < 32:
                import warnings

                warnings.warn(  # noqa: B028
                    "SECRET_KEY should be at least 32 characters even in development"
                )  # noqa: B028

        return self

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "staging", "production", "testing"]
        v = v.lower()
        if v not in valid_envs:
            raise ValueError(f"ENVIRONMENT must be one of {valid_envs}")
        return v

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy.

        Returns:
            str: Database connection string.
        """
        return self.DATABASE_URL

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes.

        Returns:
            int: Maximum file size in bytes.
        """
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production.

        Returns:
            bool: True if production environment.
        """
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development.

        Returns:
            bool: True if development environment.
        """
        return self.ENVIRONMENT == "development"

    def get_storage_config(self) -> dict:
        """Get storage configuration based on USE_S3 flag.

        Returns:
            dict: Storage configuration.
        """
        if self.USE_S3:
            return {
                "type": "s3",
                "bucket": self.AWS_S3_BUCKET,
                "region": self.AWS_S3_REGION,
                "access_key": self.AWS_ACCESS_KEY_ID,
                "secret_key": self.AWS_SECRET_ACCESS_KEY,
            }
        else:
            return {
                "type": "minio",
                "endpoint": self.MINIO_ENDPOINT,
                "bucket": self.MINIO_BUCKET,
                "access_key": self.MINIO_ACCESS_KEY,
                "secret_key": self.MINIO_SECRET_KEY,
                "secure": self.MINIO_SECURE,
            }


# Global settings instance
settings = Settings()


# Validate settings on import
if __name__ != "__main__":
    # Log configuration summary (only in non-production)
    if settings.ENVIRONMENT != "production":
        from loguru import logger

        logger.info(f"Configuration loaded for environment: {settings.ENVIRONMENT}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
        logger.info(f"Redis: {settings.REDIS_URL.split('@')[-1]}")
        logger.info(f"Storage: {settings.get_storage_config()['type']}")
