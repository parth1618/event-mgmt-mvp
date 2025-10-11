"""Initial migration with all tables, indexes, and seed data

Revision ID: 001
Revises:
Create Date: 2025-10-11 12:00:00.000000

"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables with proper indexes and insert seed data."""

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, default="attendee"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # Create categories table
    op.create_table(
        "categories",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])
    op.create_index("ix_categories_is_active", "categories", ["is_active"])

    # Create events table
    op.create_table(
        "events",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organizer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_datetime", sa.DateTime(), nullable=False),
        sa.Column("end_datetime", sa.DateTime(), nullable=False),
        sa.Column("timezone", sa.String(50), nullable=False, default="UTC"),
        sa.Column("venue_name", sa.String(255), nullable=False),
        sa.Column("venue_address", sa.String(500), nullable=False),
        sa.Column("venue_city", sa.String(100), nullable=False),
        sa.Column("venue_state", sa.String(100), nullable=True),
        sa.Column("venue_country", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("banner_url", sa.String(500), nullable=True),
        sa.Column("total_capacity", sa.Integer(), nullable=False),
        sa.Column("available_capacity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="draft"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, default=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["organizer_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_events_title", "events", ["title"])
    op.create_index("ix_events_slug", "events", ["slug"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_start_datetime", "events", ["start_datetime"])
    op.create_index("ix_events_category_id", "events", ["category_id"])
    op.create_index("ix_events_organizer_id", "events", ["organizer_id"])
    op.create_index("ix_events_is_featured", "events", ["is_featured"])
    op.create_index("ix_events_venue_city", "events", ["venue_city"])

    # Create tickets table
    op.create_table(
        "tickets",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity_total", sa.Integer(), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False),
        sa.Column("min_per_order", sa.Integer(), nullable=False, default=1),
        sa.Column("max_per_order", sa.Integer(), nullable=False, default=10),
        sa.Column("sale_start_date", sa.DateTime(), nullable=True),
        sa.Column("sale_end_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tickets_event_id", "tickets", ["event_id"])
    op.create_index("ix_tickets_price", "tickets", ["price"])

    # Create orders table
    op.create_table(
        "orders",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("order_number", sa.String(50), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("payment_status", sa.String(20), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_orders_order_number", "orders", ["order_number"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_event_id", "orders", ["event_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_payment_status", "orders", ["payment_status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])

    # Create order_items table
    op.create_table(
        "order_items",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])
    op.create_index("ix_order_items_ticket_id", "order_items", ["ticket_id"])

    # Create payments table
    op.create_table(
        "payments",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
        ),
        sa.Column(
            "order_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True
        ),
        sa.Column(
            "stripe_payment_intent_id", sa.String(255), nullable=False, unique=True
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, default="usd"),
        sa.Column("status", sa.String(20), nullable=False, default="pending"),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index(
        "ix_payments_stripe_payment_intent_id", "payments", ["stripe_payment_intent_id"]
    )
    op.create_index("ix_payments_status", "payments", ["status"])

    # Insert seed data - Categories
    categories_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Music",
            "slug": "music",
            "description": "Concerts, festivals, and live performances",
            "icon": "🎵",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Business",
            "slug": "business",
            "description": "Conferences, networking, and professional development",
            "icon": "💼",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Technology",
            "slug": "technology",
            "description": "Tech meetups, hackathons, and workshops",
            "icon": "💻",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Food & Drink",
            "slug": "food-drink",
            "description": "Tastings, cooking classes, and culinary events",
            "icon": "🍽️",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sports & Fitness",
            "slug": "sports-fitness",
            "description": "Races, tournaments, and fitness classes",
            "icon": "⚽",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Arts & Culture",
            "slug": "arts-culture",
            "description": "Exhibitions, theater, and cultural events",
            "icon": "🎨",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Education",
            "slug": "education",
            "description": "Classes, seminars, and educational workshops",
            "icon": "📚",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Health & Wellness",
            "slug": "health-wellness",
            "description": "Yoga, meditation, and wellness retreats",
            "icon": "🧘",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Community",
            "slug": "community",
            "description": "Local gatherings and community events",
            "icon": "🤝",
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Entertainment",
            "slug": "entertainment",
            "description": "Comedy shows, movies, and entertainment",
            "icon": "🎭",
        },
    ]

    op.bulk_insert(
        sa.table(
            "categories",
            sa.column("id", postgresql.UUID),
            sa.column("name", sa.String),
            sa.column("slug", sa.String),
            sa.column("description", sa.Text),
            sa.column("icon", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        ),
        [
            {
                "id": uuid.UUID(cat["id"]),
                "name": cat["name"],
                "slug": cat["slug"],
                "description": cat["description"],
                "icon": cat["icon"],
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            for cat in categories_data
        ],
    )

    # Insert seed data - Admin user (password: Admin123!)
    admin_id = uuid.uuid4()
    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", postgresql.UUID),
            sa.column("email", sa.String),
            sa.column("hashed_password", sa.String),
            sa.column("first_name", sa.String),
            sa.column("last_name", sa.String),
            sa.column("role", sa.String),
            sa.column("is_active", sa.Boolean),
            sa.column("is_verified", sa.Boolean),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
        ),
        [
            {
                "id": admin_id,
                "email": "admin@event-mgmt-mvp.com",
                "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5gy4hCfZvIiEi",
                "first_name": "System",
                "last_name": "Administrator",
                "role": "admin",
                "is_active": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ],
    )


def downgrade() -> None:
    """Drop all tables in correct order (respecting foreign keys)."""
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("tickets")
    op.drop_table("events")
    op.drop_table("categories")
    op.drop_table("users")
