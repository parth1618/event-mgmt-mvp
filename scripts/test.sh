#!/bin/bash
set -e

echo "🧪 Running tests..."

# Format code
echo "🎨 Formatting code..."
uv run black app tests

# Sort imports
echo "📦 Sorting imports..."
uv run isort app tests

# Type check
echo "🔍 Type checking..."
uv run mypy app

# Run tests with coverage
echo "✅ Running tests..."
uv run pytest --cov=app --cov-report=html --cov-report=term -v

# Security check
echo "🔒 Security check..."
uv run bandit -r app -ll

echo "✅ All tests passed!"