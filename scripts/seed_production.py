"""Seed production database with essential categories and admin user.

This script should be run ONCE on production setup to create:
- Production event categories
- System administrator account

Usage:
    python scripts/seed_production.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from uuid import uuid4

from loguru import logger

from app.config import settings
from app.core.security import hash_password
from app.database import async_session_maker
from app.models.category import Category
from app.models.user import User


async def seed_categories():
    """Seed production event categories."""
    categories = [
        {
            "name": "Music",
            "slug": "music",
            "description": "Concerts, festivals, and live music performances",
            "icon": "🎵",
        },
        {
            "name": "Business & Professional",
            "slug": "business",
            "description": "Conferences, networking events, and professional development",
            "icon": "💼",
        },
        {
            "name": "Technology & Innovation",
            "slug": "technology",
            "description": "Tech meetups, hackathons, workshops, and innovation showcases",
            "icon": "💻",
        },
        {
            "name": "Food & Drink",
            "slug": "food-drink",
            "description": "Food festivals, tastings, cooking classes, and culinary experiences",
            "icon": "🍽️",
        },
        {
            "name": "Sports & Fitness",
            "slug": "sports-fitness",
            "description": "Races, tournaments, fitness classes, and sporting events",
            "icon": "⚽",
        },
        {
            "name": "Arts & Culture",
            "slug": "arts-culture",
            "description": "Art exhibitions, theater performances, and cultural festivals",
            "icon": "🎨",
        },
        {
            "name": "Education & Learning",
            "slug": "education",
            "description": "Classes, seminars, workshops, and educational programs",
            "icon": "📚",
        },
        {
            "name": "Health & Wellness",
            "slug": "health-wellness",
            "description": "Yoga, meditation, wellness retreats, and health seminars",
            "icon": "🧘",
        },
        {
            "name": "Community & Social",
            "slug": "community",
            "description": "Local gatherings, meetups, and community building events",
            "icon": "🤝",
        },
        {
            "name": "Entertainment",
            "slug": "entertainment",
            "description": "Comedy shows, movies, gaming, and entertainment events",
            "icon": "🎭",
        },
        {
            "name": "Family & Kids",
            "slug": "family-kids",
            "description": "Family-friendly events, kids activities, and educational fun",
            "icon": "👨‍👩‍👧‍👦",
        },
        {
            "name": "Charity & Causes",
            "slug": "charity",
            "description": "Fundraisers, charity events, and social impact initiatives",
            "icon": "❤️",
        },
    ]

    async with async_session_maker() as session:
        created_count = 0

        for cat_data in categories:
            # Check if category already exists
            from sqlalchemy import select

            result = await session.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(
                    f"Category '{cat_data['name']}' already exists, skipping..."
                )
                continue

            # Create category
            category = Category(
                id=uuid4(),
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                icon=cat_data["icon"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(category)
            created_count += 1
            logger.info(f"Created category: {cat_data['name']}")

        await session.commit()
        logger.success(
            f"✓ Seeded {created_count} categories (skipped {len(categories) - created_count} existing)"
        )


async def create_admin_user():
    """Create system administrator account."""
    admin_email = "admin@event-mgmt-mvp.com"
    admin_password = "Admin123!"  # CHANGE THIS IN PRODUCTION!

    async with async_session_maker() as session:
        # Check if admin exists
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == admin_email))
        existing = result.scalar_one_or_none()

        if existing:
            logger.warning(f"⚠️  Admin user '{admin_email}' already exists")
            return

        # Create admin user
        admin = User(
            id=uuid4(),
            email=admin_email,
            hashed_password=hash_password(admin_password),
            first_name="System",
            last_name="Administrator",
            role="admin",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(admin)
        await session.commit()

        logger.success(f"✓ Created admin user: {admin_email}")
        logger.warning("⚠️  IMPORTANT: Change the admin password immediately!")
        logger.info(f"   Default password: {admin_password}")


async def verify_seed():
    """Verify seeded data."""
    async with async_session_maker() as session:
        from sqlalchemy import func, select

        # Count categories
        result = await session.execute(select(func.count()).select_from(Category))
        category_count = result.scalar()

        # Count admin users
        result = await session.execute(
            select(func.count()).select_from(User).where(User.role == "admin")
        )
        admin_count = result.scalar()

        logger.info(f"📊 Database Status:")
        logger.info(f"   Categories: {category_count}")
        logger.info(f"   Admin users: {admin_count}")


async def main():
    """Main seeding function."""
    logger.info("🌱 Starting production database seeding...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    if settings.ENVIRONMENT == "production":
        logger.warning("⚠️  Running in PRODUCTION environment!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted by user")
            return

    try:
        # Seed categories
        logger.info("Creating event categories...")
        await seed_categories()

        # Create admin user
        logger.info("Creating admin user...")
        await create_admin_user()

        # Verify
        await verify_seed()

        logger.success("✅ Production seeding completed successfully!")

        if settings.ENVIRONMENT == "production":
            logger.warning("")
            logger.warning("🔐 SECURITY CHECKLIST:")
            logger.warning("   1. Change admin password immediately")
            logger.warning("   2. Update SECRET_KEY in environment")
            logger.warning("   3. Update Stripe keys to live mode")
            logger.warning("   4. Configure email service (SendGrid)")
            logger.warning("   5. Enable HTTPS in production")
            logger.warning("   6. Configure monitoring (Sentry)")

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
