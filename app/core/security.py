"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.config import settings

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


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
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
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token.
    
    Args:
        data: Data to encode in token.
        
    Returns:
        str: Encoded JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token.
    
    Args:
        token: JWT token to verify.
        
    Returns:
        Dict[str, Any]: Decoded token payload.
        
    Raises:
        JWTError: If token is invalid or expired.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Verify and decode refresh token.
    
    Args:
        token: Refresh token to verify.
        
    Returns:
        Dict[str, Any]: Decoded token payload.
        
    Raises:
        JWTError: If token is invalid or not a refresh token.
    """
    payload = verify_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload