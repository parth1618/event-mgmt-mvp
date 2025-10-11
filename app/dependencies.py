"""FastAPI dependencies for authentication and authorization."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository
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
        user_id_str: str | None = payload.get("sub")

        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert string to UUID
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

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
            detail="Not enough permissions. Organizer role required.",
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get user from token if provided, None otherwise.

    Args:
        credentials: Optional HTTP Bearer token.
        db: Database session.

    Returns:
        User | None: User if token is valid, None otherwise.
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id_str = payload.get("sub")

        if user_id_str is None:
            return None

        user_id = UUID(user_id_str)
        user_repo = UserRepository(db)
        user = await user_repo.get(user_id)

        if user and user.is_active:
            return user
        return None
    except (JWTError, ValueError):
        return None
