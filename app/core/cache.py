"""Redis cache manager with connection pooling and circuit breaker."""

import json
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis
from loguru import logger

from app.config import settings


class CircuitBreaker:
    """Simple circuit breaker for Redis connections."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.is_open = False

    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.is_open = False

    def record_failure(self):
        """Record failed operation."""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        import time

        if not self.is_open:
            return True

        if time.time() - self.last_failure_time > self.timeout:
            logger.info("Circuit breaker half-open, attempting reconnection")
            self.is_open = False
            self.failure_count = 0
            return True

        return False


class CacheManager:
    """Redis cache manager with async support and resilience features."""

    def __init__(self) -> None:
        """Initialize cache manager."""
        self._redis: redis.Redis | None = None
        self._connected = False
        self.circuit_breaker = CircuitBreaker()

    async def connect(self) -> None:
        """Establish Redis connection with connection pooling."""
        if not self.circuit_breaker.can_attempt():
            logger.warning("Circuit breaker open, skipping Redis connection")
            return

        try:
            # Create connection pool
            pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )

            self._redis = redis.Redis(connection_pool=pool)
            await self._redis.ping()
            self._connected = True
            self.circuit_breaker.record_success()
            logger.info("Redis cache connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            self.circuit_breaker.record_failure()

    async def disconnect(self) -> None:
        """Close Redis connection gracefully."""
        if self._redis:
            await self._redis.aclose()
            self._connected = False
            logger.info("Redis cache disconnected")

    @asynccontextmanager
    async def _safe_operation(self):
        """Context manager for safe Redis operations with automatic reconnection."""
        if not self._redis or not self._connected:
            await self.connect()

        try:
            yield
            self.circuit_breaker.record_success()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            self.circuit_breaker.record_failure()
            self._connected = False
            raise
        except Exception as e:
            logger.error(f"Redis operation error: {e}")
            raise

    async def ping(self) -> bool:
        """Check if Redis is responsive.

        Returns:
            bool: True if Redis responds, False otherwise.
        """
        try:
            async with self._safe_operation():
                await self._redis.ping()
                return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def get(self, key: str) -> Any | None:
        """Get value from cache with automatic deserialization.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        if not self._connected:
            return None

        try:
            async with self._safe_operation():
                value = await self._redis.get(key)
                if value:
                    return json.loads(value)
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in cache with options.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
            nx: Only set if key doesn't exist.
            xx: Only set if key exists.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self._connected:
            return False

        try:
            async with self._safe_operation():
                ttl = ttl or settings.CACHE_TTL_SECONDS
                serialized = json.dumps(value, default=str)

                result = await self._redis.set(
                    key,
                    serialized,
                    ex=ttl,
                    nx=nx,
                    xx=xx,
                )
                return bool(result)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache.

        Args:
            *keys: Cache keys to delete.

        Returns:
            int: Number of keys deleted.
        """
        if not self._connected or not keys:
            return 0

        try:
            async with self._safe_operation():
                return await self._redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return 0

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*").

        Returns:
            int: Number of keys deleted.
        """
        if not self._connected:
            return 0

        try:
            async with self._safe_operation():
                keys = []
                async for key in self._redis.scan_iter(match=pattern, count=100):
                    keys.append(key)

                if keys:
                    return await self._redis.delete(*keys)
                return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    async def exists(self, *keys: str) -> int:
        """Check if keys exist in cache.

        Args:
            *keys: Cache keys to check.

        Returns:
            int: Number of keys that exist.
        """
        if not self._connected or not keys:
            return 0

        try:
            async with self._safe_operation():
                return await self._redis.exists(*keys)
        except Exception as e:
            logger.error(f"Cache exists check error: {e}")
            return 0

    async def increment(self, key: str, amount: int = 1) -> int | None:
        """Increment counter in cache.

        Args:
            key: Cache key.
            amount: Amount to increment.

        Returns:
            New value or None on error.
        """
        if not self._connected:
            return None

        try:
            async with self._safe_operation():
                return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None

    async def get_many(self, *keys: str) -> dict[str, Any]:
        """Get multiple values from cache.

        Args:
            *keys: Cache keys.

        Returns:
            dict: Dictionary of key-value pairs.
        """
        if not self._connected or not keys:
            return {}

        try:
            async with self._safe_operation():
                values = await self._redis.mget(*keys)
                result = {}
                for key, value in zip(keys, values):  # noqa: B905
                    if value:
                        try:
                            result[key] = json.loads(value)
                        except json.JSONDecodeError:
                            result[key] = value
                return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs.
            ttl: Time to live in seconds.

        Returns:
            bool: True if successful.
        """
        if not self._connected or not mapping:
            return False

        try:
            async with self._safe_operation():
                pipe = self._redis.pipeline()
                ttl = ttl or settings.CACHE_TTL_SECONDS

                for key, value in mapping.items():
                    serialized = json.dumps(value, default=str)
                    pipe.setex(key, ttl, serialized)

                await pipe.execute()
                return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key.

        Args:
            key: Cache key.

        Returns:
            int: TTL in seconds, -1 if key exists but no TTL, -2 if key doesn't exist.
        """
        if not self._connected:
            return -2

        try:
            async with self._safe_operation():
                return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2


# Global cache manager instance
cache_manager = CacheManager()
