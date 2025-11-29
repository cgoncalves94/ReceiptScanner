# Receipt Scanner

A modern Python API for analyzing receipt images using AI. Built with **FastAPI**, **Pydantic AI**, and **Gemini Vision**.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (for PostgreSQL)
- [Gemini API key](https://aistudio.google.com/apikey)

### Setup

```bash
# Clone and enter project
git clone https://github.com/cgoncalves94/receipt-scanner.git
cd receipt-scanner

# Start PostgreSQL
docker compose up -d db

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Run migrations and start server
make dev
```

The API is now running at <http://localhost:8000>

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Common Commands

```bash
make install    # Install dependencies
make dev        # Run migrations + start server (hot reload)
make test       # Run test suite with coverage
make lint       # Run linter and formatter
make migrate    # Apply database migrations
make help       # Show all commands
```

## Project Structure

```text
app/
├── main.py              # FastAPI app entry point
├── core/                # Shared infrastructure (config, db, exceptions)
├── receipt/             # Receipt domain
│   ├── router.py        # API endpoints
│   ├── models.py        # SQLModel + Pydantic schemas
│   ├── services.py      # Business logic
│   └── deps.py          # Dependency injection
├── category/            # Category domain (same structure)
└── integrations/
    └── pydantic_ai/     # Gemini Vision AI integration
```

Each domain is **self-contained** with its own router, models, services, and dependencies.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL (async) |
| AI | Pydantic AI + Gemini Vision |
| Migrations | Alembic |
| Testing | Pytest (async) |
| Code Quality | Ruff, Pre-commit |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/receipts/scan` | Upload and analyze receipt image |
| `GET` | `/api/v1/receipts` | List all receipts |
| `GET` | `/api/v1/receipts/{id}` | Get receipt by ID |
| `PATCH` | `/api/v1/receipts/{id}` | Update receipt |
| `POST` | `/api/v1/categories` | Create category |
| `GET` | `/api/v1/categories` | List categories |
| `GET` | `/api/v1/categories/{id}` | Get category |
| `PATCH` | `/api/v1/categories/{id}` | Update category |
| `DELETE` | `/api/v1/categories/{id}` | Delete category |

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide.

## License

See [LICENSE](LICENSE) file.
