# Development Guide

Detailed guide for developing the Receipt Scanner API.

## Prerequisites

- **Python 3.14+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** - Fast Python package manager
- **Docker** - For PostgreSQL database
- **Gemini API Key** - Get one at <https://aistudio.google.com/apikey>

## Initial Setup

### 1. Clone and Install

```bash
git clone https://github.com/cgoncalves94/receipt-scanner.git
cd receipt-scanner

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
make install-dev
```

### 2. Start Database

```bash
# Start PostgreSQL container
make db-up

# Verify it's running
docker compose ps
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```bash
GEMINI_API_KEY=your_api_key_here
```

### 4. Run the Application

```bash
# Apply migrations and start server with hot reload
make dev
```

The API is available at <http://localhost:8000>

## Daily Development

### Running the Server

```bash
make dev      # With migrations (recommended)
make run      # Without migrations
```

### Running Tests

```bash
make test     # Run all tests
make test-cov # Run with coverage report
```

### Code Quality

```bash
make lint     # Check for issues
make format   # Auto-fix and format
```

Pre-commit hooks are recommended:

```bash
pre-commit install
```

## Database

### Migrations

```bash
make migrate                    # Apply pending migrations
make migration m='add users'    # Create new migration
make migrate-down               # Rollback one migration
make migrate-history            # View migration history
```

### Direct Alembic Commands

```bash
uv run alembic current          # Current revision
uv run alembic heads            # Latest available
uv run alembic downgrade base   # Reset all migrations
```

## Project Architecture

### Vertical Slice Structure

Each domain is self-contained:

```text
app/
├── main.py                 # FastAPI app, lifespan, middleware
├── models.py               # SQLModel registry (for Alembic)
├── core/                   # Shared infrastructure
│   ├── config.py           # Settings from environment
│   ├── db.py               # Database engine and sessions
│   ├── deps.py             # Shared dependencies (get_session)
│   ├── exceptions.py       # Custom exception classes
│   ├── error_handlers.py   # Exception → HTTP response mapping
│   └── decorators.py       # @transactional decorator
├── receipt/                # Receipt domain
│   ├── router.py           # API endpoints (/api/v1/receipts)
│   ├── models.py           # Receipt, ReceiptItem models + schemas
│   ├── services.py         # Business logic
│   └── deps.py             # ReceiptDeps injection
├── category/               # Category domain (same structure)
└── integrations/
    └── pydantic_ai/        # AI integration
        ├── receipt_agent.py    # Pydantic AI agent
        ├── receipt_schema.py   # Response schemas
        └── receipt_prompt.py   # System prompts
```

### Key Patterns

#### Dependency Injection

```python
# deps.py
ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

# router.py
@router.get("/{id}")
async def get_receipt(id: int, service: ReceiptDeps):
    return await service.get(id)
```

#### Exception Handling

```python
# Raise domain exceptions
raise NotFoundError(f"Receipt {id} not found")

# Automatically mapped to HTTP 404
```

#### Transactional Decorator

```python
@transactional
async def create_from_scan(self, image: UploadFile) -> Receipt:
    # All operations in a single transaction
    # Automatic rollback on failure
```

## Docker

### Full Stack

```bash
make docker-up      # Start db + app
make docker-down    # Stop all
make docker-logs    # View logs
```

### Database Only

```bash
make db-up          # Start PostgreSQL
make db-down        # Stop PostgreSQL
```

### Rebuild

```bash
make docker-build   # Rebuild and start
```

## Testing

### Test Structure

```text
tests/
├── conftest.py             # Shared fixtures
├── unit/                   # Unit tests (mocked dependencies)
│   ├── category/
│   ├── receipt/
│   └── core/
└── integration/            # API tests (real database)
    ├── category/
    └── receipt/
```

### Running Specific Tests

```bash
# Single file
uv run pytest tests/unit/receipt/test_receipt_service.py -v

# Single test
uv run pytest tests/unit/receipt/test_receipt_service.py::test_create_receipt -v

# By marker
uv run pytest -m asyncio -v
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps

# Restart database
make db-down && make db-up

# Check connection
uv run python -c "from app.core.db import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"
```

### Import Errors

```bash
# Reinstall dependencies
make clean
make install
```

### Migration Conflicts

```bash
# Reset to clean state (WARNING: deletes data)
uv run alembic downgrade base
uv run alembic upgrade head
```
