"""Category schemas."""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base category schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating category."""
    
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating category."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryOut(CategoryBase):
    """Schema for category response."""
    
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}