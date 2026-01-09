# Receipt Scanner

A full-stack receipt scanning application with AI-powered analysis. Upload receipts, extract items automatically, and track spending by category.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16, React 19, TanStack Query, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, SQLModel, Pydantic AI, PostgreSQL |
| **AI** | Google Gemini Vision |

## Quick Start

### Prerequisites

- Python 3.14+
- Node.js 20+
- Docker (for PostgreSQL)
- [Gemini API key](https://aistudio.google.com/apikey)

### Setup

```bash
# Clone and enter project
git clone https://github.com/cgoncalves94/receipt-scanner.git
cd receipt-scanner

# Run setup (installs deps, creates .env)
make setup

# Add your GEMINI_API_KEY to backend/.env

# Start database + backend
make dev

# In another terminal, start frontend
make dev-frontend
```

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

### Common Commands

```bash
# Development
make dev              # Start db + backend
make dev-frontend     # Start frontend

# Testing
make test             # Run backend tests
make test-frontend    # Run frontend tests

# Docker (full stack)
make up               # Start all services
make down             # Stop all services
make logs             # View logs

# Utilities
make setup            # Initial setup
make clean            # Remove caches
make help             # Show all commands
```

## Project Structure

```text
receipt-scanner/
├── backend/                # FastAPI Python backend
│   ├── app/
│   │   ├── core/           # Config, db, exceptions
│   │   ├── receipt/        # Receipt domain
│   │   ├── category/       # Category domain
│   │   └── integrations/   # AI integration
│   └── tests/
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/            # App Router pages
│       ├── components/     # React components
│       ├── hooks/          # TanStack Query hooks
│       └── lib/            # API client, utilities
├── docker-compose.yml
└── Makefile
```

## Features

- **AI Receipt Scanning**: Upload receipt images, get items extracted automatically
- **Category Management**: Organize items with custom categories
- **Multi-Currency Support**: Track spending in EUR, GBP, USD with real-time conversion
- **Analytics Dashboard**: Monthly spending breakdown by category
- **Dark Mode**: Modern dark-first UI design

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/receipts/scan` | Upload and analyze receipt |
| `GET` | `/api/v1/receipts` | List receipts |
| `GET` | `/api/v1/receipts/{id}` | Get receipt details |
| `PATCH` | `/api/v1/receipts/{id}` | Update receipt |
| `DELETE` | `/api/v1/receipts/{id}` | Delete receipt |
| `PATCH` | `/api/v1/receipts/{id}/items/{itemId}` | Update item |
| `GET` | `/api/v1/categories` | List categories |
| `POST` | `/api/v1/categories` | Create category |
| `PATCH` | `/api/v1/categories/{id}` | Update category |
| `DELETE` | `/api/v1/categories/{id}` | Delete category |

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide.

## License

See [LICENSE](LICENSE) file.
