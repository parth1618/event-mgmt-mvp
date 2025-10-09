"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.schemas.user import UserCreate, UserOut, Token, PasswordResetRequest, PasswordReset, TokenRefresh
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Register a new user.
    
    Args:
        user_data: User registration data.
        db: Database session.
        
    Returns:
        UserOut: Created user data.
        
    Raises:
        HTTPException: If email already exists.
        
    Example:
        curl -X POST "http://localhost:8000/api/v1/auth/register" \\
             -H "Content-Type: application/json" \\
             -d '{"email": "user@example.com", "password": "SecurePass123"}'
    """
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_data)
    logger.info(f"User registered: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login and get access token.
    
    Args:
        email: User email.
        password: User password.
        db: Database session.
        
    Returns:
        Token: Access and refresh tokens.
        
    Raises:
        HTTPException: If credentials are invalid.
        
    Example:
        curl -X POST "http://localhost:8000/api/v1/auth/login" \\
             -H "Content-Type: application/x-www-form-urlencoded" \\
             -d "email=user@example.com&password=SecurePass123"
    """
    auth_service = AuthService(db)
    token = await auth_service.login(email, password)
    logger.info(f"User logged in: {email}")
    return token


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Refresh access token using refresh token.
    
    Args:
        refresh_data: Refresh token data.
        db: Database session.
        
    Returns:
        Token: New access and refresh tokens.
        
    Raises:
        HTTPException: If refresh token is invalid.
    """
    auth_service = AuthService(db)
    token = await auth_service.refresh_token(refresh_data.refresh_token)
    return token


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request password reset (stubbed - logs instead of sending email).
    
    Args:
        request: Password reset request with email.
        db: Database session.
        
    Returns:
        dict: Success message.
        
    Example:
        curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \\
             -H "Content-Type: application/json" \\
             -d '{"email": "user@example.com"}'
    """
    auth_service = AuthService(db)
    await auth_service.request_password_reset(request.email)
    logger.info(f"Password reset requested for: {request.email}")
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset password using token.
    
    Args:
        reset_data: Reset token and new password.
        db: Database session.
        
    Returns:
        dict: Success message.
        
    Raises:
        HTTPException: If token is invalid or expired.
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(reset_data.token, reset_data.new_password)
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    """Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        UserOut: User data.
        
    Example:
        curl -X GET "http://localhost:8000/api/v1/auth/me" \\
             -H "Authorization: Bearer <token>"
    """
    return current_user