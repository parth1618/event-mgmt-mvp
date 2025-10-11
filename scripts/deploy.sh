#!/bin/bash
set -e

echo "🚀 Deploying Event Mgmt MVP..."

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t event-mgmt-mvp:latest .

# Tag for registry
REGISTRY=${REGISTRY:-"your-registry.com"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
docker tag event-mgmt-mvp:latest $REGISTRY/event-mgmt-mvp:$IMAGE_TAG

# Push to registry
echo "📤 Pushing to registry..."
docker push $REGISTRY/event-mgmt-mvp:$IMAGE_TAG

# Deploy with docker-compose
echo "🚀 Deploying services..."
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
echo "🗄️  Running migrations..."
docker-compose -f docker-compose.prod.yml exec -T api uv run alembic upgrade head

# Health check
echo "🏥 Health check..."
sleep 5
curl -f http://localhost:8000/health || { echo "❌ Health check failed"; exit 1; }

echo "✅ Deployment successful!"