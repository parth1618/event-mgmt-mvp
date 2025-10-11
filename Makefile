.PHONY: help install setup start stop test lint format clean migrate backup deploy
.DEFAULT_GOAL := help

# Colors for output
# BLUE := \033[0;34m
# GREEN := \033[0;32m
# YELLOW := \033[0;33m
# RED := \033[0;31m
# NC := \033[0m # No Color
ifeq ($(OS),Windows_NT)
    BLUE  := 
    GREEN := 
    YELLOW:= 
    RED   := 
    NC    := 
else
    BLUE  := \033[0;34m
    GREEN := \033[0;32m
    YELLOW:= \033[0;33m
    RED   := \033[0;31m
    NC    := \033[0m
endif

help: ## Show this help message
	@echo '$(BLUE)Event Management MVP - Development Commands$(NC)'
	@echo ''
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==============================================================================
# Installation & Setup
# ==============================================================================

install: ## Install dependencies with UV
	@echo "$(BLUE)Installing dependencies with UV...$(NC)"
	uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-prod: ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv pip install -e .
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

setup: ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	bash scripts/setup.sh
	@echo "$(GREEN)✓ Setup complete$(NC)"

setup-hooks: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	uv run pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

# ==============================================================================
# Docker Operations
# ==============================================================================

start: ## Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "MinIO Console: http://localhost:9001"

stop: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: stop start ## Restart all services

logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs only
	docker-compose logs -f app

status: ## Show status of all services
	docker-compose ps

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Images built$(NC)"

down: ## Stop and remove containers, networks, volumes
	@echo "$(YELLOW)Stopping and removing all containers...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# ==============================================================================
# Development Server
# ==============================================================================

dev: ## Run development server with hot reload
	@echo "$(BLUE)Starting development server...$(NC)"
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

dev-https: ## Run development server with HTTPS
	@echo "$(BLUE)Starting development server with HTTPS...$(NC)"
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8443 --ssl-keyfile=./certs/key.pem --ssl-certfile=./certs/cert.pem

# ==============================================================================
# Testing
# ==============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated: htmlcov/index.html$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	uv run pytest -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	uv run pytest -m integration

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests...$(NC)"
	uv run pytest -m e2e

test-fast: ## Run tests without slow tests
	@echo "$(BLUE)Running fast tests...$(NC)"
	uv run pytest -m "not slow"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	uv run pytest-watch

# ==============================================================================
# Code Quality
# ==============================================================================

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run black app tests
	uv run isort app tests
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Run all Ruff lint checks
	@echo "$(BLUE)Running Ruff lint checks...$(NC)"
	uv run ruff check app tests
	uv run mypy app
	@echo "$(GREEN)✓ Linting complete$(NC)"

lint-fix: ## Run Ruff with auto-fix
	@echo "$(BLUE)Running Ruff auto-fix...$(NC)"
	uv run ruff check --fix app tests
	@echo "$(GREEN)✓ Ruff auto-fix complete$(NC)"

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	uv run bandit -r app -ll
	uv run safety check
	@echo "$(GREEN)✓ Security checks complete$(NC)"

check: format lint security test ## Run all quality checks

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	uv run pre-commit run --all-files

# ==============================================================================
# Database Operations
# ==============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	uv run alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

migrate-create: ## Create new migration
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"
	@echo "$(GREEN)✓ Migration created$(NC)"

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	uv run alembic downgrade -1
	@echo "$(GREEN)✓ Rollback complete$(NC)"

migrate-history: ## Show migration history
	uv run alembic history

migrate-current: ## Show current migration version
	uv run alembic current

db-shell: ## Open database shell
	docker-compose exec db psql -U eventbrite -d eventbrite_mvp

db-dump: ## Dump database to file
	@echo "$(BLUE)Dumping database...$(NC)"
	docker-compose exec -T db pg_dump -U eventbrite eventbrite_mvp > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database dumped$(NC)"

db-restore: ## Restore database from file (usage: make db-restore FILE=backup.sql)
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	docker-compose exec -T db psql -U eventbrite eventbrite_mvp < $(FILE)
	@echo "$(GREEN)✓ Database restored$(NC)"

# ==============================================================================
# Redis Operations
# ==============================================================================

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

redis-flush: ## Flush all Redis data
	@echo "$(YELLOW)Flushing all Redis data...$(NC)"
	docker-compose exec redis redis-cli FLUSHALL
	@echo "$(GREEN)✓ Redis flushed$(NC)"

redis-info: ## Show Redis info
	docker-compose exec redis redis-cli INFO

# ==============================================================================
# Celery Operations
# ==============================================================================

celery-worker: ## Start Celery worker
	@echo "$(BLUE)Starting Celery worker...$(NC)"
	uv run celery -A app.tasks.celery_app worker --loglevel=info

celery-beat: ## Start Celery beat scheduler
	@echo "$(BLUE)Starting Celery beat...$(NC)"
	uv run celery -A app.tasks.celery_app beat --loglevel=info

celery-flower: ## Start Celery Flower (monitoring)
	@echo "$(BLUE)Starting Celery Flower...$(NC)"
	uv run celery -A app.tasks.celery_app flower --port=5555
	@echo "Flower UI: http://localhost:5555"

celery-purge: ## Purge all Celery tasks
	@echo "$(YELLOW)Purging all Celery tasks...$(NC)"
	uv run celery -A app.tasks.celery_app purge
	@echo "$(GREEN)✓ Tasks purged$(NC)"

celery-status: ## Show Celery workers status
	uv run celery -A app.tasks.celery_app status

# ==============================================================================
# Seeding & Demo Data
# ==============================================================================

seed: ## Seed database with demo data
	@echo "$(BLUE)Seeding database...$(NC)"
	uv run python scripts/seed_data.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

seed-prod: ## Seed production categories and admin
	@echo "$(BLUE)Seeding production data...$(NC)"
	uv run python scripts/seed_production.py
	@echo "$(GREEN)✓ Production data seeded$(NC)"

# ==============================================================================
# Cleanup
# ==============================================================================

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	rm -rf logs/*.log 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean down ## Clean everything including Docker volumes
	@echo "$(YELLOW)Removing all Docker volumes...$(NC)"
	docker volume prune -f
	@echo "$(GREEN)✓ Complete cleanup done$(NC)"

# ==============================================================================
# Backup & Restore
# ==============================================================================

backup: ## Create full backup (DB + Redis + MinIO)
	@echo "$(BLUE)Creating full backup...$(NC)"
	bash scripts/backup.sh
	@echo "$(GREEN)✓ Backup complete$(NC)"

restore: ## Restore from backup (usage: make restore BACKUP=backup.tar.gz)
	@echo "$(YELLOW)Restoring from $(BACKUP)...$(NC)"
	bash scripts/restore.sh $(BACKUP)
	@echo "$(GREEN)✓ Restore complete$(NC)"

# ==============================================================================
# Development Utilities
# ==============================================================================

shell: ## Open Python shell with app context
	@echo "$(BLUE)Opening Python shell...$(NC)"
	uv run ipython

shell-async: ## Open async Python shell
	@echo "$(BLUE)Opening async Python shell...$(NC)"
	uv run python -m asyncio

generate-secret: ## Generate secure secret key
	@echo "$(BLUE)Generated SECRET_KEY:$(NC)"
	@uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

create-user: ## Create new user interactively
	@echo "$(BLUE)Creating new user...$(NC)"
	uv run python scripts/create_user.py

# ==============================================================================
# Documentation
# ==============================================================================

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "Documentation available at: http://localhost:8000/docs"
	@echo "ReDoc available at: http://localhost:8000/redoc"

docs-export: ## Export OpenAPI schema
	@echo "$(BLUE)Exporting OpenAPI schema...$(NC)"
	uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
	@echo "$(GREEN)✓ Schema exported to openapi.json$(NC)"

# ==============================================================================
# Deployment
# ==============================================================================

deploy-staging: ## Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(NC)"
	bash scripts/deploy.sh staging
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

deploy-prod: ## Deploy to production environment
	@echo "$(YELLOW)Deploying to production...$(NC)"
	bash scripts/deploy.sh production
	@echo "$(GREEN)✓ Deployed to production$(NC)"

health-check: ## Check application health
	@echo "$(BLUE)Checking application health...$(NC)"
	@curl -f http://localhost:8000/api/v1/health || (echo "$(RED)✗ Health check failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Application healthy$(NC)"

# ==============================================================================
# Performance & Monitoring
# ==============================================================================

profile: ## Profile application performance
	@echo "$(BLUE)Profiling application...$(NC)"
	uv run python -m cProfile -o profile.stats scripts/profile_app.py
	@echo "$(GREEN)✓ Profile saved to profile.stats$(NC)"

load-test: ## Run load tests with Locust
	@echo "$(BLUE)Running load tests...$(NC)"
	uv run locust -f tests/load_test.py --host=http://localhost:8000
	@echo "Locust UI: http://localhost:8089"

# ==============================================================================
# CI/CD
# ==============================================================================

ci: format lint security test ## Run CI pipeline locally
	@echo "$(GREEN)✓ CI pipeline complete$(NC)"

ci-docker: ## Run CI in Docker
	@echo "$(BLUE)Running CI in Docker...$(NC)"
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit
	@echo "$(GREEN)✓ Docker CI complete$(NC)"

# ==============================================================================
# Information
# ==============================================================================

info: ## Show project information
	@echo "$(BLUE)=== Event Management MVP ===$(NC)"
	@echo "Python version: $(shell python --version)"
	@echo "UV version: $(shell uv --version)"
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo ""
	@echo "Services:"
	@docker-compose ps 2>/dev/null || echo "  Services not running"

version: ## Show application version
	@uv run python -c "from app.config import settings; print(f'Version: {settings.VERSION}')"