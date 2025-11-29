.PHONY: help install dev run test test-unit test-integration test-all test-cov db-test-setup db-test-teardown lint format migrate clean docker-up docker-down

# Default target
help:
	@echo "Receipt Scanner - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     Install all dependencies"
	@echo "  make install-dev Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev         Run migrations + start server (hot reload)"
	@echo "  make run         Start server without migrations"
	@echo ""
	@echo "Testing:"
	@echo "  make test            Run unit tests (no database required)"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests (auto-creates test_db)"
	@echo "  make test-all        Run all tests (auto-creates test_db)"
	@echo "  make test-cov        Run tests with coverage report"
	@echo "  make db-test-setup   Create test database"
	@echo "  make db-test-teardown Drop test database"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint        Check code with ruff"
	@echo "  make format      Format code with ruff"
	@echo "  make typecheck   Run mypy type checking"
	@echo ""
	@echo "Database:"
	@echo "  make migrate     Apply database migrations"
	@echo "  make migration   Create new migration (usage: make migration m='description')"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up   Start all services (db + app)"
	@echo "  make docker-down Stop all services"
	@echo "  make db-up       Start database only"
	@echo "  make db-down     Stop database"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       Remove cache and build files"

# ============================================================================
# Setup
# ============================================================================

install:
	uv sync

install-dev:
	uv sync --all-extras

# ============================================================================
# Development
# ============================================================================

dev: migrate
	uv run uvicorn app.main:app --reload

run:
	uv run uvicorn app.main:app --reload

test: test-unit

test-unit:
	uv run pytest tests/unit/ -v --tb=short

test-integration: db-test-setup
	uv run pytest tests/integration/ -v --tb=short
	@$(MAKE) db-test-teardown

test-all: db-test-setup
	uv run pytest tests/ -v --tb=short
	@$(MAKE) db-test-teardown

test-cov: db-test-setup
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	@$(MAKE) db-test-teardown
	@echo "Coverage report: open htmlcov/index.html"

db-test-setup:
	@echo "🔧 Setting up test database..."
	@docker exec receipt-postgres psql -U postgres -c "DROP DATABASE IF EXISTS test_db;" -q
	@docker exec receipt-postgres psql -U postgres -c "CREATE DATABASE test_db;" -q
	@echo "✅ Test database ready"

db-test-teardown:
	@echo "🧹 Cleaning up test database..."
	@docker exec receipt-postgres psql -U postgres -c "DROP DATABASE IF EXISTS test_db;" -q
	@echo "✅ Test database removed"

lint:
	uv run ruff check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy app/

# ============================================================================
# Database
# ============================================================================

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(m)"

migrate-down:
	uv run alembic downgrade -1

migrate-history:
	uv run alembic history

# ============================================================================
# Docker
# ============================================================================

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose up --build -d

db-up:
	docker compose up -d db

db-down:
	docker compose down db

docker-logs:
	docker compose logs -f

# ============================================================================
# Cleanup
# ============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
