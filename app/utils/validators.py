"""Custom Pydantic validators."""

import re
from typing import Any
from pydantic import field_validator


def validate_password_strength(password: str) -> str:
    """Validate password meets security requirements.
    
    Args:
        password: Password to validate.
        
    Returns:
        str: Validated password.
        
    Raises:
        ValueError: If password doesn't meet requirements.
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    
    return password


def validate_phone_number(phone: str) -> str:
    """Validate phone number format.
    
    Args:
        phone: Phone number to validate.
        
    Returns:
        str: Validated phone number.
        
    Raises:
        ValueError: If phone number is invalid.
    """
    # Simple validation - can be enhanced with phonenumbers library
    cleaned = re.sub(r"[^\d+]", "", phone)
    if len(cleaned) < 10:
        raise ValueError("Invalid phone number")
    return cleaned


def validate_slug(slug: str) -> str:
    """Validate URL slug format.
    
    Args:
        slug: Slug to validate.
        
    Returns:
        str: Validated slug.
        
    Raises:
        ValueError: If slug is invalid.
    """
    if not re.match(r"^[a-z0-9-]+$", slug):
        raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
    return slug