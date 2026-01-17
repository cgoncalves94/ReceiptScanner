# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

Receipt Scanner is a full-stack application for scanning receipts with AI-powered item extraction. Users upload receipt images, get items automatically extracted with categories, and track spending.

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, TanStack Query, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, SQLModel, Pydantic AI, PostgreSQL (async) |
| **AI** | Google Gemini Vision |

## Project Structure (Monorepo)

```text
receipt-scanner/
├── backend/                # FastAPI Python backend
│   ├── app/
│   │   ├── main.py         # App entry, lifespan, middleware
│   │   ├── core/           # Config, db, exceptions, decorators
│   │   ├── auth/           # Auth domain (router, models, services, deps)
│   │   ├── receipt/        # Receipt domain (router, models, services, deps)
│   │   ├── category/       # Category domain
│   │   ├── analytics/      # Analytics domain (spending summaries, trends, breakdowns)
│   │   └── integrations/   # AI integration (pydantic_ai/)
│   ├── tests/              # Unit and integration tests
│   └── migrations/         # Alembic migrations
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/(app)/      # App routes (dashboard, receipts, categories, analytics, scan)
│       ├── components/ui/  # shadcn/ui components
│       ├── hooks/          # TanStack Query hooks
│       ├── lib/api/        # API client
│       └── types/          # TypeScript types
├── docker-compose.yml
└── Makefile
```

## Build & Development Commands

```bash
# From root (recommended)
make dev              # Start db + backend (hot reload)
make dev-frontend     # Start frontend (port 3000)
make test             # Run all backend tests (auto-starts db)
make test-unit        # Run unit tests only (no db needed)
make test-integration # Run integration tests (auto-starts db)
make test-cov         # Run tests with coverage report
make setup            # Initial setup

# Backend (cd backend) - for quick local commands
make dev              # Run migrations + start server
make test             # Run unit tests
make check            # Run lint + typecheck
make format           # Auto-fix

# Frontend (cd frontend)
pnpm dev              # Start dev server
pnpm build            # Production build
pnpm lint             # ESLint

# Database migrations (cd backend)
make migrate                    # Apply migrations
make migration m='description'  # Create migration
```

## Backend Architecture

**Vertical Slice** - Each domain is self-contained:

```text
backend/app/
├── core/
│   ├── config.py           # pydantic-settings
│   ├── db.py               # Async SQLModel engine
│   ├── deps.py             # get_session dependency
│   ├── exceptions.py       # NotFoundError, ConflictError, etc.
│   ├── error_handlers.py   # Exception → HTTP response (standard FastAPI format)
│   └── decorators.py       # @transactional
├── auth/
│   ├── router.py           # /api/v1/auth endpoints
│   ├── models.py           # User + schemas
│   ├── services.py         # AuthService (register/login)
│   └── deps.py             # CurrentUser dependency
├── receipt/
│   ├── router.py           # /api/v1/receipts endpoints
│   ├── models.py           # Receipt, ReceiptItem + schemas
│   ├── services.py         # ReceiptService (business logic)
│   └── deps.py             # ReceiptDeps = Annotated[ReceiptService, Depends(...)]
├── category/               # Same structure
├── analytics/              # Analytics domain (no models - query-only)
│   ├── router.py           # /api/v1/analytics endpoints
│   ├── models.py           # Response schemas (SpendingSummary, SpendingTrend, etc.)
│   ├── services.py         # AnalyticsService (aggregation queries)
│   └── deps.py             # AnalyticsDeps
└── integrations/pydantic_ai/
    ├── receipt_agent.py    # Pydantic AI agent with Gemini
    ├── receipt_schema.py   # ReceiptAnalysis response schema
    └── receipt_prompt.py   # System prompts
```

### Key Backend Patterns

**Dependency Injection:**

```python
ReceiptDeps = Annotated[ReceiptService, Depends(get_receipt_service)]

@router.get("/{id}")
async def get_receipt(id: int, service: ReceiptDeps): ...
```

**Exception Handling (standard FastAPI format):**

```python
raise NotFoundError(f"Receipt {id} not found")   # → 404 {"detail": "..."}
raise ConflictError("Category has items")         # → 409 {"detail": "..."}
```

**Transactional Decorator:**

```python
@transactional
async def create_from_scan(self, image: UploadFile) -> Receipt:
    # All operations in single transaction, auto-rollback on error
```

## Frontend Architecture

```text
frontend/src/
├── app/(app)/              # Route group for authenticated pages
│   ├── page.tsx            # Dashboard (monthly stats, recent receipts)
│   ├── receipts/           # List + [id] detail
│   ├── categories/         # CRUD management
│   ├── analytics/          # Spending charts by category
│   └── scan/               # Receipt upload with drag-drop
├── hooks/
│   ├── use-receipts.ts     # useReceipts, useReceipt, useScanReceipt, useDeleteReceipt, useUpdateReceiptItem, useCreateReceiptItem, useDeleteReceiptItem
│   ├── use-categories.ts   # useCategories, useCreateCategory, useDeleteCategory, useCategoryItems
│   ├── use-analytics.ts    # useAnalyticsSummary, useAnalyticsTrends, useTopStores, useCategoryBreakdown
│   └── use-currency.ts     # useExchangeRates (Frankfurter API)
├── lib/api/client.ts       # ApiClient class with typed methods
└── components/ui/          # shadcn/ui (Button, Card, Dialog, AlertDialog, Select, etc.)
```

### Key Frontend Patterns

**TanStack Query hooks:**

```typescript
const { data, isLoading } = useReceipts();
const deleteMutation = useDeleteReceipt();
await deleteMutation.mutateAsync(id);
```

**Optimistic updates with cache manipulation:**

```typescript
onMutate: async (id) => {
  await queryClient.cancelQueries({ queryKey: [...RECEIPTS_KEY, id] });
  queryClient.removeQueries({ queryKey: [...RECEIPTS_KEY, id] });
}
```

**Mutation reset after error:**

```typescript
catch (error) {
  toast.error(error.message);
  deleteMutation.reset();  // Required to allow retry
}
```

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and receive JWT |
| `GET` | `/api/v1/auth/me` | Get current user |
| `POST` | `/api/v1/receipts/scan` | Upload and analyze receipt |
| `GET` | `/api/v1/receipts` | List receipts (supports filtering: search, store, after, before, category_ids, min_amount, max_amount) |
| `GET` | `/api/v1/receipts/{id}` | Get receipt with items |
| `PATCH` | `/api/v1/receipts/{id}` | Update receipt |
| `DELETE` | `/api/v1/receipts/{id}` | Delete receipt |
| `PATCH` | `/api/v1/receipts/{id}/items/{itemId}` | Update item (name, category) |
| `POST` | `/api/v1/receipts/{id}/items` | Create new item |
| `DELETE` | `/api/v1/receipts/{id}/items/{itemId}` | Delete item |
| `GET` | `/api/v1/receipts/category/{id}/items` | List items by category |
| `GET` | `/api/v1/categories` | List categories |
| `POST` | `/api/v1/categories` | Create category |
| `PATCH` | `/api/v1/categories/{id}` | Update category |
| `DELETE` | `/api/v1/categories/{id}` | Delete category (fails if has items) |
| `GET` | `/api/v1/analytics/summary` | Spending summary (year, month params) |
| `GET` | `/api/v1/analytics/trends` | Spending trends (start, end, period params) |
| `GET` | `/api/v1/analytics/top-stores` | Top stores by spending (year, month, limit params) |
| `GET` | `/api/v1/analytics/category-breakdown` | Spending by category (year, month params) |

## Testing

**Backend:**

```bash
cd backend && make test
# Or specific: uv run pytest tests/unit/receipt/test_receipt_service.py -v
```

**Frontend:** Tests not yet configured (placeholder script).

## Code Quality

- **Backend:** Ruff (lint + format), ty (strict), pre-commit hooks
- **Frontend:** ESLint, TypeScript strict

## Environment

**Backend (`backend/.env`):**

- `GEMINI_API_KEY` (required)
- `JWT_SECRET_KEY` (required, min 32 chars; validated at startup)
- `GEMINI_MODEL` (default: gemini-2.5-flash-preview-05-20)
- `POSTGRES_*` (defaults work with docker-compose)

**Frontend:**

- `NEXT_PUBLIC_API_URL` (default: <http://localhost:8000>)

## Important Notes

1. **Error responses** use standard FastAPI format: `{"detail": "message"}`
2. **Category deletion** is protected - fails with 409 if items are assigned
3. **TanStack Query mutations** need `.reset()` after errors to allow retry
4. **Delete operations** use `onMutate` for optimistic cache removal to prevent 404 race conditions
5. **Currency storage** uses ISO 4217 codes (EUR, GBP, USD) - displayed as symbols (€, £, $) in frontend
6. **Multi-currency analytics** - backend returns `totals_by_currency` arrays, frontend converts using Frankfurter API
7. **Date formatting** uses ISO 8601 (`isoformat()`) for Safari compatibility
8. **JWT secret** is validated at startup; set `JWT_SECRET_KEY` in backend/.env
