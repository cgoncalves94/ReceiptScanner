# Receipt Scanner API

A modern FastAPI application for scanning and analyzing receipts using Google's Gemini Vision API, built with clean architecture and robust production patterns.

## Architecture Overview

This project implements a clean, layered architecture with several modern design patterns working in harmony:

### Key Architectural Patterns

#### 1. Clean Architecture
- **API Layer**: FastAPI routes and endpoints
- **Service Layer**: Business logic and orchestration
- **Repository Layer**: Data access abstraction
- **Domain Layer**: SQLModel/Pydantic models

#### 2. Database Patterns
- **Repository Pattern**: Clean data access abstraction
- **Unit of Work**: Transaction management via session handling
- **Nested Transactions**: SAVEPOINT support for complex operations
- **SQLModel Integration**: Unified ORM and API schemas

#### 3. Dependency Management
- **Dependency Injection**: FastAPI's dependency system
- **Service Factory Pattern**: Dynamic service instantiation
- **Session Management**: Automated lifecycle handling
- **Resource Cleanup**: Proper connection and session handling

#### 4. Error Handling
- **Global Exception Handlers**: Consistent error responses
- **Database Error Mapping**: Clean SQL error translation
- **Transaction Rollback**: Automatic on failure
- **Type Safety**: Comprehensive type hints

#### 5. Async Architecture
- **Non-blocking Operations**: Fully async from API to database
- **Concurrent Processing**: Efficient handling of parallel requests
- **Resource Management**: Proper async context handling
- **Event-driven Design**: Async service communication

#### 6. Computer Vision & AI Pipeline
- **Image Processing**: Advanced cleaning and perspective correction
- **Gemini Vision API**: Intelligent text extraction and analysis
- **Multi-stage Pipeline**: Combined CV preprocessing and AI analysis
- **Prompt Engineering**: Structured data extraction from raw text

### Project Structure
```
app/
├── api/          # REST endpoints, route handlers, and request/response models
├── core/         # Application core: config, DB setup, exceptions, decorators
├── integrations/ # External service integrations
├── middlewares/  # Request/response middleware, error handlers, auth
├── models/       # Domain models combining SQLModel (ORM) and Pydantic schemas
├── repositories/ # Data access layer with database operations
├── services/     # Business logic and service orchestration
└── main.py       # Application bootstrap and configuration
```

### Development Environment

- **Docker**: Containerized development environment
- **Pre-commit**: Code quality hooks and formatting
- **UV**: Modern Python package management
- **Ruff**: Fast Python linting

## Quick Start

### 1. Start Database
```bash
# Start PostgreSQL database
docker compose up db -d
```

### 2. Install Dependencies
```bash
# Create and activate virtual environment
uv venv
```

```bash
# Install all dependencies (including dev tools)
uv pip install -r requirements.txt
```

### 3. Setup Environment
```bash
cp .env.example .env
```
Then edit `.env` with your settings.

### 4. Run Application

Start the development server (recommended):
```bash
bash scripts/start-dev.sh
```

Or manually with uvicorn:
```bash
uv run -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively, run everything with Docker Compose:
```bash
# Run both database and application
docker compose up -d
```

## Development

### Dependency Management

Add new dependencies (updates pyproject.toml):
```bash
uv pip install package_name
```

After adding dependencies, update requirements.txt:
```bash
pip-compile pyproject.toml
```

View installed packages:
```bash
uv pip list
```

### Pre-commit hooks

Install hooks:
```bash
pre-commit install
```

Run hooks manually:
```bash
pre-commit run --all-files
```
