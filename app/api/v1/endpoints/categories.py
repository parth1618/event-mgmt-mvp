"""Category management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.dependencies import get_current_admin
from app.models.user import User
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("", response_model=List[CategoryOut])
async def list_categories(
    db: AsyncSession = Depends(get_db),
) -> List[CategoryOut]:
    """List all categories.
    
    Args:
        db: Database session.
        
    Returns:
        List[CategoryOut]: List of categories.
    """
    category_service = CategoryService(db)
    categories = await category_service.list_categories()
    return categories


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CategoryOut:
    """Create a new category (admin only).
    
    Args:
        category_data: Category creation data.
        current_user: Current authenticated admin.
        db: Database session.
        
    Returns:
        CategoryOut: Created category data.
    """
    category_service = CategoryService(db)
    category = await category_service.create_category(category_data)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: UUID,
    category_update: CategoryUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CategoryOut:
    """Update category (admin only).
    
    Args:
        category_id: Category UUID.
        category_update: Updated category data.
        current_user: Current authenticated admin.
        db: Database session.
        
    Returns:
        CategoryOut: Updated category data.
    """
    category_service = CategoryService(db)
    category = await category_service.update_category(category_id, category_update)
    return category