#!/bin/bash
set -e

echo "🧪 Running tests..."

# Format code
echo "🎨 Formatting code..."
poetry run black app tests

# Sort imports
echo "📦 Sorting imports..."
poetry run isort app tests

# Type check
echo "🔍 Type checking..."
poetry run mypy app

# Run tests with coverage
echo "✅ Running tests..."
poetry run pytest --cov=app --cov-report=html --cov-report=term -v

# Security check
echo "🔒 Security check..."
poetry run bandit -r app -ll

echo "✅ All tests passed!"