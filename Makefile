.PHONY: help dev dev-backend dev-frontend build up down logs test test-unit test-integration test-cov test-frontend test-db-ready clean db-up db-down init setup stop-port-conflicts

# Docker compose uses directory name as project name (enables worktree isolation)
COMPOSE := docker compose

# Default target
help:
	@echo "Receipt Scanner Monorepo - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make dev            Start all services (db + backend)"
	@echo "  make dev-backend    Start backend only (requires db running)"
	@echo "  make dev-frontend   Start frontend only (requires backend running)"
	@echo ""
	@echo "Docker:"
	@echo "  make build          Build all Docker images"
	@echo "  make up             Start all services in Docker"
	@echo "  make down           Stop all services"
	@echo "  make logs           View logs from all services"
	@echo "  make db-up          Start database only"
	@echo "  make db-down        Stop database"
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run all backend tests (auto-starts db)"
	@echo "  make test-unit         Run unit tests only (no db needed)"
	@echo "  make test-integration  Run integration tests (auto-starts db)"
	@echo "  make test-cov          Run tests with coverage report"
	@echo "  make test-frontend     Run frontend tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          Remove cache and build files"
	@echo "  make init           Start backend + frontend"
	@echo "  make setup          Initial setup (install deps, create .env)"

# ============================================================================
# Development
# ============================================================================

dev: db-up
	@echo "Starting backend..."
	cd backend && make dev

dev-backend:
	cd backend && make dev

dev-frontend:
	cd frontend && pnpm dev

# ============================================================================
# Docker
# ============================================================================

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

# Get current project name (docker compose lowercases directory name)
PROJECT_NAME := $(shell basename $(CURDIR) | tr '[:upper:]' '[:lower:]')

# Stop container on port 5432 only if it belongs to a different project (enables worktree switching)
stop-port-conflicts:
	@container=$$(docker ps -q --filter "publish=5432"); \
	if [ -n "$$container" ]; then \
		container_project=$$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' $$container 2>/dev/null); \
		if [ "$$container_project" = "$(PROJECT_NAME)" ]; then \
			echo "Database container already running for this project"; \
		else \
			echo "Stopping container from project '$$container_project' on port 5432..."; \
			docker stop $$container >/dev/null; \
		fi; \
	fi

db-up: stop-port-conflicts
	@$(COMPOSE) up -d db --wait
	@echo "Database ready"

db-down:
	$(COMPOSE) down db

# ============================================================================
# Testing
# ============================================================================

# Ensure test database exists (idempotent)
test-db-ready: stop-port-conflicts
	@$(COMPOSE) up -d db --wait
	@$(COMPOSE) exec -T db psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'test_db'" | grep -q 1 || \
		$(COMPOSE) exec -T db psql -U postgres -c "CREATE DATABASE test_db;" >/dev/null
	@echo "Test database ready"

# Run all backend tests (ensures db is ready)
test: test-db-ready
	cd backend && uv run pytest tests/ -v --tb=short

# Run only unit tests (no db required)
test-unit:
	cd backend && uv run pytest tests/unit/ -v --tb=short

# Run only integration tests (requires db)
test-integration: test-db-ready
	cd backend && uv run pytest tests/integration/ -v --tb=short

# Run tests with coverage
test-cov: test-db-ready
	cd backend && uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: open backend/htmlcov/index.html"

test-frontend:
	cd frontend && pnpm test

# ============================================================================
# Setup
# ============================================================================

init:
	@echo "Starting backend and frontend..."
	@echo "   (use Ctrl+C to stop both)"
	@$(MAKE) -j2 dev dev-frontend

setup:
	@echo "Setting up Receipt Scanner..."
	@echo ""
	@echo "1. Installing backend dependencies..."
	cd backend && make install-dev
	@echo ""
	@echo "2. Installing frontend dependencies..."
	cd frontend && pnpm install
	@echo ""
	@echo "3. Creating backend .env file..."
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "   Created backend/.env - please add your GEMINI_API_KEY"; \
	else \
		echo "   backend/.env already exists"; \
	fi
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "  1. Add your GEMINI_API_KEY to backend/.env"
	@echo "  2. Run 'make dev' to start the backend"
	@echo "  3. Run 'make dev-frontend' to start the frontend"

# ============================================================================
# Cleanup
# ============================================================================

clean:
	cd backend && make clean
	@if [ -d frontend/node_modules ]; then \
		echo "Cleaning frontend..."; \
		cd frontend && rm -rf .next node_modules; \
	fi
	$(COMPOSE) down -v --remove-orphans 2>/dev/null || true
