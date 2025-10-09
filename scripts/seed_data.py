"""Seed database with test data for development."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.database import async_session_maker
from app.models.user import User
from app.models.category import Category
from app.models.event import Event
from app.models.ticket import Ticket
from app.core.security import get_password_hash
from loguru import logger


async def seed_categories():
    """Seed event categories."""
    categories = [
        {"name": "Music", "slug": "music", "icon": "🎵"},
        {"name": "Business", "slug": "business", "icon": "💼"},
        {"name": "Technology", "slug": "technology", "icon": "💻"},
        {"name": "Food & Drink", "slug": "food-drink", "icon": "🍽️"},
        {"name": "Sports", "slug": "sports", "icon": "⚽"},
        {"name": "Arts", "slug": "arts", "icon": "🎨"},
    ]
    
    async with async_session_maker() as session:
        for cat_data in categories:
            category = Category(**cat_data)
            session.add(category)
        await session.commit()
        logger.info(f"Seeded {len(categories)} categories")


async def seed_users():
    """Seed test users."""
    users = [
        {
            "email": "organizer@test.com",
            "password": "OrganizerPass123!",
            "full_name": "Test Organizer",
            "role": "organizer",
        },
        {
            "email": "attendee@test.com",
            "password": "AttendeePass123!",
            "full_name": "Test Attendee",
            "role": "attendee",
        },
    ]
    
    async with async_session_maker() as session:
        for user_data in users:
            password = user_data.pop("password")
            user = User(
                **user_data,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_verified=True
            )
            session.add(user)
        await session.commit()
        logger.info(f"Seeded {len(users)} users")


async def seed_events():
    """Seed sample events with tickets."""
    async with async_session_maker() as session:
        # Get organizer and category
        from sqlalchemy import select
        
        organizer = (await session.execute(
            select(User).where(User.email == "organizer@test.com")
        )).scalar_one()
        
        tech_category = (await session.execute(
            select(Category).where(Category.slug == "technology")
        )).scalar_one()
        
        music_category = (await session.execute(
            select(Category).where(Category.slug == "music")
        )).scalar_one()
        
        # Create events
        events_data = [
            {
                "title": "Tech Conference 2024",
                "description": "Annual technology conference featuring industry leaders",
                "category_id": tech_category.id,
                "location": "San Francisco Convention Center",
                "start_datetime": datetime.utcnow() + timedelta(days=30),
                "end_datetime": datetime.utcnow() + timedelta(days=30, hours=8),
                "total_capacity": 500,
                "tickets": [
                    {"name": "Early Bird", "price": Decimal("199.00"), "quantity": 100},
                    {"name": "Regular", "price": Decimal("299.00"), "quantity": 300},
                    {"name": "VIP", "price": Decimal("499.00"), "quantity": 100},
                ]
            },
            {
                "title": "Summer Music Festival",
                "description": "3-day outdoor music festival",
                "category_id": music_category.id,
                "location": "Central Park, New York",
                "start_datetime": datetime.utcnow() + timedelta(days=60),
                "end_datetime": datetime.utcnow() + timedelta(days=63),
                "total_capacity": 5000,
                "tickets": [
                    {"name": "General Admission", "price": Decimal("99.00"), "quantity": 4000},
                    {"name": "VIP Pass", "price": Decimal("299.00"), "quantity": 1000},
                ]
            },
        ]
        
        for event_data in events_data:
            tickets_data = event_data.pop("tickets")
            
            event = Event(
                **event_data,
                organizer_id=organizer.id,
                available_capacity=event_data["total_capacity"],
                status="published",
                published_at=datetime.utcnow()
            )
            session.add(event)
            await session.flush()
            
            # Create tickets
            for ticket_data in tickets_data:
                ticket = Ticket(
                    event_id=event.id,
                    **ticket_data,
                    quantity_available=ticket_data["quantity"],
                    quantity_total=ticket_data["quantity"],
                    min_per_order=1,
                    max_per_order=10
                )
                session.add(ticket)
        
        await session.commit()
        logger.info(f"Seeded {len(events_data)} events with tickets")


async def main():
    """Run all seed functions."""
    logger.info("Starting database seeding...")
    
    await seed_categories()
    await seed_users()
    await seed_events()
    
    logger.info("✅ Database seeding completed!")
    logger.info("\nTest credentials:")
    logger.info("  Organizer: organizer@test.com / OrganizerPass123!")
    logger.info("  Attendee: attendee@test.com / AttendeePass123!")


if __name__ == "__main__":
    asyncio.run(main())