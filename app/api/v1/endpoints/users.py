"""User management endpoints."""

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Get current user profile.

    Args:
        current_user: Current authenticated user.

    Returns:
        UserOut: User profile data.
    """
    return current_user


@router.put("/me", response_model=UserOut)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Update current user profile.

    Args:
        user_update: Updated user data.
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        UserOut: Updated user data.
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_update)
    return updated_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete current user account.

    Args:
        current_user: Current authenticated user.
        db: Database session.
    """
    user_service = UserService(db)
    await user_service.delete_user(current_user.id)


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Upload user avatar image.

    Args:
        file: Avatar image file (JPEG, PNG, max 5MB).
        current_user: Current authenticated user.
        db: Database session.

    Returns:
        UserOut: Updated user data with avatar URL.

    Raises:
        HTTPException: If file is invalid.
    """
    user_service = UserService(db)
    updated_user = await user_service.upload_avatar(current_user.id, file)
    return updated_user
