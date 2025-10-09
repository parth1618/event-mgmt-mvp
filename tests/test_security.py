"""Security and authentication tests."""

import pytest
from datetime import timedelta

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
    from app.core.security import create_access_token
    from app.config import settings
    import jwt
    
    data = {"sub": "test@example.com"}
    token = create_access_token(data)
    
    # Decode token
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    assert payload["sub"] == "test@example.com"
    assert "exp" in payload

def test_token_expiration():
    """Test that tokens expire."""
    from app.core.security import create_access_token
    from app.config import settings
    import jwt
    import time
    
    # Create token that expires in 1 second
    data = {"sub": "test@example.com"}
    token = create_access_token(data, expires_delta=timedelta(seconds=1))
    
    # Wait for expiration
    time.sleep(2)
    
    # Try to decode expired token
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )