"""FastAPI dependencies for authentication and authorization."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.database import get_db
from app.core.security import verify_token
from app.repositories.user import UserRepository
from app.models.user import User
from app.utils.constants import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token from request header.
        db: Database session.
        
    Returns:
        User: Current authenticated user.
        
    Raises:
        HTTPException: If token is invalid or user not found.
        
    Example:
        @app.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
            return user
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_organizer(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require current user to be an organizer or admin.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        User: Current user if they are organizer or admin.
        
    Raises:
        HTTPException: If user is not organizer or admin.
    """
    if current_user.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Organizer role required."
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require current user to be an admin.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        User: Current user if they are admin.
        
    Raises:
        HTTPException: If user is not admin.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[str]:
    """Get user ID from token if provided, None otherwise.
    
    Args:
        credentials: Optional HTTP Bearer token.
        
    Returns:
        Optional[str]: User ID if token is valid, None otherwise.
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        return payload.get("sub")
    except JWTError:
        return None