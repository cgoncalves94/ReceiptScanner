# Development Guide

Detailed guide for developing the Receipt Scanner full-stack application.

## Prerequisites

- **Python 3.14+**
- **Node.js 20+** and **pnpm**
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **Docker** - For PostgreSQL database
- **Gemini API Key** - Get one at <https://aistudio.google.com/apikey>

## Initial Setup

### Quick Setup

```bash
# Install everything and create .env
make setup

# Add your API key to backend/.env
echo "GEMINI_API_KEY=your_key" >> backend/.env

# Start development
make dev              # Terminal 1: Backend
make dev-frontend     # Terminal 2: Frontend
```

### Manual Setup

```bash
# 1. Install backend dependencies
cd backend && uv sync --all-extras

# 2. Install frontend dependencies
cd frontend && pnpm install

# 3. Start database
docker compose up -d db

# 4. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add GEMINI_API_KEY

# 5. Run migrations
cd backend && uv run alembic upgrade head

# 6. Start services
cd backend && uv run uvicorn app.main:app --reload  # Terminal 1
cd frontend && pnpm dev                              # Terminal 2
```

## Development Workflow

### Backend Development

```bash
cd backend

# Daily development
make dev          # Run migrations + start server with hot reload
make run          # Start server without migrations

# Testing
make test         # Run unit tests
make test-cov     # Run with coverage report

# Code quality
make lint         # Check with ruff + mypy
make format       # Auto-fix and format

# Database
make migrate                    # Apply pending migrations
make migration m='add_field'    # Create new migration
make migrate-down               # Rollback one migration
```

### Frontend Development

```bash
cd frontend

# Development
pnpm dev          # Start with hot reload (port 3000)

# Build
pnpm build        # Production build
pnpm start        # Run production build

# Quality
pnpm lint         # Run ESLint
```

### Full Stack (from root)

```bash
make dev              # Start db + backend
make dev-frontend     # Start frontend
make test             # Run all tests
make clean            # Remove all caches
```

## Project Architecture

### Backend (Vertical Slice)

Each domain is self-contained:

```text
backend/app/
├── main.py                 # FastAPI app, lifespan, middleware
├── core/                   # Shared infrastructure
│   ├── config.py           # Settings (pydantic-settings)
│   ├── db.py               # Async database engine/sessions
│   ├── deps.py             # Shared dependencies
│   ├── exceptions.py       # Domain exceptions
│   ├── error_handlers.py   # Exception → HTTP mapping
│   └── decorators.py       # @transactional decorator
├── receipt/                # Receipt domain
│   ├── router.py           # API endpoints
│   ├── models.py           # SQLModel models + schemas
│   ├── services.py         # Business logic
│   └── deps.py             # Domain dependencies
├── category/               # Category domain (same structure)
└── integrations/
    └── pydantic_ai/        # Gemini AI integration
```

### Frontend

```text
frontend/src/
├── app/                    # Next.js App Router
│   ├── (app)/              # Authenticated routes
│   │   ├── page.tsx        # Dashboard
│   │   ├── receipts/       # Receipt pages
│   │   ├── categories/     # Category management
│   │   ├── analytics/      # Spending analytics
│   │   └── scan/           # Receipt scanning
│   └── layout.tsx          # Root layout
├── components/
│   └── ui/                 # shadcn/ui components
├── hooks/                  # TanStack Query hooks
│   ├── use-receipts.ts     # Receipt mutations/queries
│   ├── use-categories.ts   # Category mutations/queries
│   └── use-currency.ts     # Currency conversion
├── lib/
│   ├── api/client.ts       # API client
│   └── format.ts           # Formatters
└── types/                  # TypeScript types
```

## Key Patterns

### Backend: Dependency Injection

```python
# deps.py
ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

# router.py
@router.get("/{id}")
async def get_receipt(id: int, service: ReceiptDeps):
    return await service.get(id)
```

### Backend: Exception Handling

```python
# Raise domain exceptions - automatically mapped to HTTP
raise NotFoundError(f"Receipt {id} not found")  # → 404
raise ConflictError("Category has items")        # → 409
```

### Frontend: TanStack Query

```typescript
// Queries
const { data, isLoading } = useReceipts();

// Mutations with optimistic updates
const deleteMutation = useDeleteReceipt();
await deleteMutation.mutateAsync(id);
```

## Database

### Migrations

```bash
cd backend

make migrate                    # Apply migrations
make migration m='description'  # Create new migration
make migrate-down               # Rollback one
make migrate-history            # View history
```

### Direct Alembic

```bash
cd backend
uv run alembic current          # Current revision
uv run alembic heads            # Latest available
uv run alembic downgrade base   # Reset all (WARNING: deletes data)
```

## Testing

### Backend Tests

```text
backend/tests/
├── unit/                   # Mocked dependencies, fast
│   ├── receipt/
│   ├── category/
│   └── core/
└── integration/            # Real database
    ├── receipt/
    └── category/
```

```bash
# Run all unit tests
cd backend && make test

# Run specific test
cd backend && uv run pytest tests/unit/receipt/test_receipt_service.py -v

# With coverage
cd backend && make test-cov
```

### Frontend Tests

```bash
cd frontend && pnpm test
# (Tests not yet configured - add Vitest when needed)
```

## Docker

### Full Stack

```bash
make build          # Build images
make up             # Start all services
make down           # Stop all
make logs           # View logs
```

### Database Only

```bash
make db-up          # Start PostgreSQL
make db-down        # Stop PostgreSQL
```

## Environment Variables

### Backend (`backend/.env`)

Required:

- `GEMINI_API_KEY` - Google Gemini API key

Optional:

- `GEMINI_MODEL` - AI model (default: `gemini-2.5-flash-preview-05-20`)
- `POSTGRES_*` - Database config (defaults work with docker-compose)
- `LOGFIRE_TOKEN` - For monitoring

### Frontend (`frontend/.env.local`)

- `NEXT_PUBLIC_API_URL` - Backend URL (default: `http://localhost:8000`)

## Troubleshooting

### Database Connection

```bash
# Check if PostgreSQL is running
docker compose ps

# Restart database
make db-down && make db-up
```

### Import Errors

```bash
# Reinstall dependencies
cd backend && uv sync --all-extras
cd frontend && pnpm install
```

### Port Conflicts

- Backend: 8000 (change in backend/Makefile)
- Frontend: 3000 (change with `pnpm dev -p 3001`)
- Database: 5432 (change in docker-compose.yml)
