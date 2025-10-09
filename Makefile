.PHONY: help install setup start stop test lint format clean migrate backup deploy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $1, $2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

setup: ## Setup development environment
	bash scripts/setup.sh

start: ## Start all services
	docker-compose up -d
	@echo "✅ Services started"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

stop: ## Stop all services
	docker-compose down

restart: stop start ## Restart all services

logs: ## View logs
	docker-compose logs -f

test: ## Run tests
	bash scripts/test.sh

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=app --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

lint: ## Run linting
	poetry run flake8 app tests
	poetry run mypy app

format: ## Format code
	poetry run black app tests
	poetry run isort app tests

clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

migrate: ## Run database migrations
	docker-compose exec api poetry run alembic upgrade head

migrate-create: ## Create new migration
	@read -p "Enter migration message: " msg; \
	docker-compose exec api poetry run alembic revision --autogenerate -m "$msg"

migrate-rollback: ## Rollback last migration
	docker-compose exec api poetry run alembic downgrade -1

db-shell: ## Open database shell
	docker-compose exec postgres psql -U postgres -d eventslake

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

backup: ## Create backup
	bash scripts/backup.sh

deploy: ## Deploy to production
	bash scripts/deploy.sh

shell: ## Open Python shell with app context
	docker-compose exec api poetry run ipython

celery-worker: ## Start Celery worker
	docker-compose exec celery-worker celery -A app.tasks.celery_app worker --loglevel=info

celery-flower: ## Start Celery Flower (monitoring)
	docker-compose exec celery-worker celery -A app.tasks.celery_app flower --port=5555

build: ## Build Docker image
	docker build -t event-mgmt-mvp:latest .

push: ## Push Docker image to registry
	docker push event-mgmt-mvp:latest

# Development helpers
dev-seed: ## Seed database with test data
	docker-compose exec api poetry run python scripts/seed_data.py

dev-reset: ## Reset database (WARNING: deletes all data)
	docker-compose exec api poetry run alembic downgrade base
	docker-compose exec api poetry run alembic upgrade head
	docker-compose exec api poetry run python scripts/seed_data.py

dev-user: ## Create test user
	@read -p "Enter email: " email; \
	read -s -p "Enter password: " password; \
	docker-compose exec api poetry run python -c "from app.models.user import User; from app.core.security import get_password_hash; from app.database import async_session_maker; import asyncio; asyncio.run((lambda: async_session_maker().begin_nested()).__call__())"
