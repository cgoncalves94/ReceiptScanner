.PHONY: help install install-dev dev run test test-integration test-cov lint format typecheck check migrate migration migrate-down migrate-history clean

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
	@echo "Testing (prefer 'make test' from project root for full setup):"
	@echo "  make test              Run unit tests (no db required)"
	@echo "  make test-integration  Run integration tests (requires db)"
	@echo "  make test-cov          Run all tests with coverage"
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

test:
	uv run pytest tests/unit/ -v --tb=short

test-integration:
	uv run pytest tests/integration/ -v --tb=short

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
