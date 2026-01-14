# Receipt Scanner

A full-stack receipt scanning application with AI-powered analysis. Upload receipts, extract items automatically, and track spending by category.

## Features

- **AI Receipt Scanning**: Upload receipt images, get items extracted automatically
- **Category Management**: Organize items with custom categories
- **User Authentication**: Register/login with JWT and per-user data isolation
- **Multi-Currency Support**: Track spending in EUR, GBP, USD with real-time conversion
- **Analytics Dashboard**: Monthly spending breakdown by category
- **Dark Mode**: Modern dark-first UI design

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| **Frontend** | Next.js 16, React 19, TanStack Query, Tailwind CSS, shadcn/ui |
| **Backend** | FastAPI, SQLModel, Pydantic AI, PostgreSQL |
| **AI** | Google Gemini Vision |

## Architecture

![Architecture](docs/architecture.png)

## Data Model

![Data Model](docs/data-model.png)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/cgoncalves94/receipt-scanner.git
cd receipt-scanner
make setup

# Add your GEMINI_API_KEY and JWT_SECRET_KEY to backend/.env
# (see backend/.env.example for required vars)

# Start services
make dev              # Terminal 1: Backend + DB
make dev-frontend     # Terminal 2: Frontend
```

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup, commands, and architecture guide.

## License

See [LICENSE](LICENSE) file.
