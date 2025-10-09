#!/bin/bash
set -e

echo "🚀 Setting up Event Mgmt MVP..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec api poetry run alembic upgrade head

# Create initial admin user
echo "👤 Creating admin user..."
docker-compose exec api poetry run python -c "
from app.database import async_session_maker
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    async with async_session_maker() as session:
        admin = User(
            email='admin@event-mgmt-mvp.com',
            hashed_password=get_password_hash('Admin123!'),
            full_name='System Administrator',
            role='admin',
            is_active=True,
            is_verified=True
        )
        session.add(admin)
        await session.commit()
        print('✅ Admin user created')

asyncio.run(create_admin())
"

echo "✅ Setup complete!"
echo ""
echo "🌐 Services:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - MinIO Console: http://localhost:9001"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "👤 Admin Login:"
echo "  - Email: admin@event-mgmt-mvp.com"
echo "  - Password: Admin123!"