.PHONY: help install dev run test test-unit test-integration test-all test-cov lint format typecheck check migrate clean

# Default target
help:
	@echo "Receipt Scanner Backend - Available Commands"
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
	@echo "  make test-integration Run integration tests"
	@echo "  make test-all        Run all tests"
	@echo "  make test-cov        Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make check       Run lint + typecheck"
	@echo "  make lint        Check code with ruff"
	@echo "  make format      Format code with ruff"
	@echo "  make typecheck   Run ty type checking"
	@echo ""
	@echo "Database:"
	@echo "  make migrate     Apply database migrations"
	@echo "  make migration   Create new migration (usage: make migration m='description')"
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

test-integration:
	uv run pytest tests/integration/ -v --tb=short

test-all:
	uv run pytest tests/ -v --tb=short

test-cov:
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: open htmlcov/index.html"

lint:
	uv run ruff check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run ty check app/

check: lint typecheck

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

# Create test database (run once, requires Docker postgres to be running)
test-db-create:
	@echo "Creating test database..."
	@docker exec receipt-postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'test_db'" | grep -q 1 || \
		docker exec receipt-postgres psql -U postgres -c "CREATE DATABASE test_db;"
	@echo "Test database ready."

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
