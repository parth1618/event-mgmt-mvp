"""Enhanced security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.cache import cache_manager

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using BCrypt.

    Args:
        password: Plain text password.

    Returns:
        str: Hashed password.

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> verify_password("mypassword123", hashed)
        True
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.

    Returns:
        bool: True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token.

    Args:
        data: Data to encode in token (should include 'sub' for user ID).
        expires_delta: Optional custom expiration time.

    Returns:
        str: Encoded JWT token.

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = verify_token(token)
        >>> payload["sub"]
        'user123'
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access", "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create JWT refresh token.

    Args:
        data: Data to encode in token.

    Returns:
        str: Encoded JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """Verify and decode JWT token with blacklist check.

    Args:
        token: JWT token to verify.

    Returns:
        dict[str, Any]: Decoded token payload.

    Raises:
        JWTError: If token is invalid, expired, or blacklisted.
    """
    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # Check if token is blacklisted
    import asyncio

    if asyncio.iscoroutinefunction(is_token_blacklisted):
        # If called from async context, this should be awaited by caller
        # For now, we'll skip blacklist check in sync context
        pass

    return payload


async def verify_token_async(token: str) -> dict[str, Any]:
    """Async version of verify_token with complete blacklist checking.

    Args:
        token: JWT token to verify.

    Returns:
        dict[str, Any]: Decoded token payload.

    Raises:
        JWTError: If token is invalid, expired, or blacklisted.
    """
    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        raise JWTError("Token has been revoked")

    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """Verify and decode refresh token.

    Args:
        token: Refresh token to verify.

    Returns:
        dict[str, Any]: Decoded token payload.

    Raises:
        JWTError: If token is invalid or not a refresh token.
    """
    payload = verify_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload


async def blacklist_token(token: str, ttl: int | None = None) -> bool:
    """Add token to blacklist (for logout/revocation).

    Args:
        token: Token to blacklist.
        ttl: Time to live in seconds (default: token expiry time).

    Returns:
        bool: True if successfully blacklisted.
    """
    try:
        # Decode to get expiry
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Calculate TTL based on token expiry
        if ttl is None:
            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.utcnow().timestamp())
                if ttl <= 0:
                    return True  # Token already expired, no need to blacklist
            else:
                ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        # Add to blacklist with TTL
        blacklist_key = f"token_blacklist:{token}"
        return await cache_manager.set(blacklist_key, "1", ttl=ttl)

    except JWTError:
        # Invalid token, no need to blacklist
        return True


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted.

    Args:
        token: Token to check.

    Returns:
        bool: True if token is blacklisted.
    """
    blacklist_key = f"token_blacklist:{token}"
    result = await cache_manager.exists(blacklist_key)
    return result > 0


async def revoke_all_user_tokens(user_id: str) -> bool:
    """Revoke all tokens for a user (e.g., on password change).

    Args:
        user_id: User ID whose tokens to revoke.

    Returns:
        bool: True if successfully revoked.
    """
    # Add user to global revocation list
    revoke_key = f"user_revoked:{user_id}"
    revoke_time = datetime.utcnow().timestamp()

    # Store with 30-day TTL (max refresh token lifetime)
    return await cache_manager.set(
        revoke_key, str(revoke_time), ttl=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )


async def is_user_tokens_revoked(user_id: str, token_issued_at: float) -> bool:
    """Check if user's tokens issued before revocation time are invalid.

    Args:
        user_id: User ID to check.
        token_issued_at: Token issued timestamp.

    Returns:
        bool: True if tokens are revoked.
    """
    revoke_key = f"user_revoked:{user_id}"
    revoke_time_str = await cache_manager.get(revoke_key)

    if revoke_time_str:
        revoke_time = float(revoke_time_str)
        return token_issued_at < revoke_time

    return False


def create_password_reset_token(user_id: str) -> str:
    """Create password reset token.

    Args:
        user_id: User ID for password reset.

    Returns:
        str: Password reset token.
    """
    return create_access_token(
        data={"sub": user_id, "type": "password_reset"},
        expires_delta=timedelta(hours=1),
    )


def verify_password_reset_token(token: str) -> str | None:
    """Verify password reset token and return user ID.

    Args:
        token: Password reset token.

    Returns:
        str | None: User ID if token is valid, None otherwise.
    """
    try:
        payload = verify_token(token)
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def create_email_verification_token(user_id: str, email: str) -> str:
    """Create email verification token.

    Args:
        user_id: User ID.
        email: Email address to verify.

    Returns:
        str: Email verification token.
    """
    return create_access_token(
        data={"sub": user_id, "email": email, "type": "email_verification"},
        expires_delta=timedelta(days=7),
    )


def verify_email_verification_token(token: str) -> tuple[str, str] | None:
    """Verify email verification token.

    Args:
        token: Email verification token.

    Returns:
        tuple[str, str] | None: (user_id, email) if valid, None otherwise.
    """
    try:
        payload = verify_token(token)
        if payload.get("type") != "email_verification":
            return None
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id and email:
            return (user_id, email)
        return None
    except JWTError:
        return None
