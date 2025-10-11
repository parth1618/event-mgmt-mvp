"""Security and authentication tests."""

from datetime import timedelta

import pytest


def test_password_hashing():
    """Test password hashing."""
    from app.core.security import get_password_hash, verify_password

    password = "TestPassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    import jwt

    from app.config import settings
    from app.core.security import create_access_token

    data = {"sub": "test@example.com"}
    token = create_access_token(data)

    # Decode token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert payload["sub"] == "test@example.com"
    assert "exp" in payload


def test_token_expiration():
    """Test that tokens expire."""
    import time

    import jwt

    from app.config import settings
    from app.core.security import create_access_token

    # Create token that expires in 1 second
    data = {"sub": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(seconds=1))

    # Wait for expiration
    time.sleep(2)

    # Try to decode expired token
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
