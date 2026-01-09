.PHONY: help dev dev-backend dev-frontend build up down logs test clean db-up db-down

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
	@echo "  make test           Run all tests"
	@echo "  make test-backend   Run backend tests"
	@echo "  make test-frontend  Run frontend tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          Remove cache and build files"
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
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

db-up:
	docker compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 3

db-down:
	docker compose down db

# ============================================================================
# Testing
# ============================================================================

test: test-backend

test-backend:
	cd backend && make test

test-frontend:
	cd frontend && pnpm test

# ============================================================================
# Setup
# ============================================================================

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
	docker compose down -v --remove-orphans 2>/dev/null || true
