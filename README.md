# Receipt Scanner

Local development setup and commands.

## Quick Start

### Install Dependencies
```bash
# Create and activate virtual environment
uv venv
```

```bash
# Install all dependencies (including dev tools)
uv pip install -r requirements.txt
```

### Setup Environment
```bash
cp .env.example .env
```
Then edit `.env` with your settings.

## Running the App

Start the development server (recommended):
```bash
bash scripts/start-dev.sh
```

Or manually with uvicorn:
```bash
uv run -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## Project Structure
```
app/
├── api/          # API routes and endpoints
├── core/         # Core business logic and utilities
├── integrations/ # Third-party service integrations
├── middlewares/  # Application middleware components
├── models/       # Database models and schemas
├── repositories/ # Data access layer
├── services/     # Business services
└── main.py       # App entry point
```
