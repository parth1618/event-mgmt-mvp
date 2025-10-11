"""Interactive CLI tool for creating users.

Usage:
    python scripts/create_user.py
"""

import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4

from loguru import logger

from app.core.security import hash_password
from app.database import async_session_maker
from app.models.user import User
from app.utils.constants import UserRole


def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    value = input(prompt).strip()
    return value if value else default


def get_password() -> str:
    """Get password with confirmation."""
    while True:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("❌ Passwords don't match. Try again.")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters.")
            continue

        return password


def get_role() -> UserRole:
    """Get user role with validation."""
    print("\nAvailable roles:")
    print("  1. attendee  - Regular user who attends events")
    print("  2. organizer - User who can create and manage events")
    print("  3. admin     - System administrator")

    while True:
        choice = input("\nSelect role (1-3) [1]: ").strip() or "1"

        role_map = {
            "1": UserRole.ATTENDEE,
            "2": UserRole.ORGANIZER,
            "3": UserRole.ADMIN,
            "attendee": UserRole.ATTENDEE,
            "organizer": UserRole.ORGANIZER,
            "admin": UserRole.ADMIN,
        }

        role = role_map.get(choice.lower())
        if role:
            return role

        print("❌ Invalid choice. Please select 1, 2, or 3.")


async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole,
    is_verified: bool = False,
) -> User:
    """Create a new user in the database."""
    async with async_session_maker() as session:
        # Check if user exists
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"User with email '{email}' already exists")

        # Create user
        user = User(
            id=uuid4(),
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=is_verified,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user


async def main():
    """Main CLI function."""
    print("=" * 60)
    print("Event Management MVP - User Creation Tool")
    print("=" * 60)
    print()

    # Get user details
    print("Enter user details:")
    print()

    email = get_user_input("Email")
    if not email:
        print("❌ Email is required")
        return

    password = get_password()

    first_name = get_user_input("First name", "")
    last_name = get_user_input("Last name", "")

    role = get_role()

    # Verify email for admin/organizer
    is_verified = role in [UserRole.ADMIN, UserRole.ORGANIZER]

    # Confirm
    print("\n" + "=" * 60)
    print("User Details:")
    print(f"  Email: {email}")
    print(f"  Name: {first_name} {last_name}")
    print(f"  Role: {role.value}")
    print(f"  Verified: {is_verified}")
    print("=" * 60)

    confirm = input("\nCreate this user? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Cancelled")
        return

    try:
        user = await create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_verified=is_verified,
        )

        print()
        print("✅ User created successfully!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role.value}")
        print()

        if role == UserRole.ADMIN:
            print("🔐 Security reminder:")
            print("   This user has full administrative privileges.")
            print("   Keep credentials secure!")

    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        print(f"❌ Failed to create user: {e}")


if __name__ == "__main__":
    asyncio.run(main())
