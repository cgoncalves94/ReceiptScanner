# Development Guide for Receipt Scanner API

This guide provides practical instructions for setting up, running, and contributing to the Receipt Scanner API project.

## Initial Setup

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- UV package manager
- Google Gemini API key

### Environment Setup

1. Clone the Repository
   ```bash
   git clone https://github.com/yourusername/receipt-scanner.git
   cd receipt-scanner
   ```

2. Start Docker Services
   ```bash
   # Build and start all services
   docker compose up --build -d

   # View logs if needed
   docker compose logs -f
   ```

3. Setup Python Environment
   ```bash
   # Create and activate virtual environment
   uv venv
   source .venv/bin/activate  # Unix/macOS
   # or
   .venv\Scripts\activate     # Windows

   # Install dependencies
   uv pip install -e ".[dev]"
   ```

4. Configure Environment
   ```bash
   cp .env.example .env
   # Edit .env with your configurations, especially the Gemini API key
   ```

## Development Workflow

### Running the Application

You can run the application using either the native command or our script:

```bash
# Using native command
uvicorn app.main:app --reload

# Or using our script
./scripts/start-dev.sh
```
The API will be available at http://localhost:8000

### Database Migrations

When modifying models (add/remove fields, create new models):

```bash
# Generate a new migration
alembic revision --autogenerate -m "describe your changes"

# Apply migrations
alembic upgrade head
# Or using our script
./scripts/db.sh

# View current state and history
alembic current
alembic history

# Rollback if needed
alembic downgrade -1
alembic downgrade <revision_id>
```

### Package Management

UV is our recommended package manager for its speed and reliability.

```bash
# Add new packages
uv pip install package_name
uv add package_name          # Also updates pyproject.toml
uv add --dev package_name    # Add dev dependency

# Manage dependencies
uv pip list                  # View installed packages
uv pip list --outdated      # Check for updates
uv pip install --upgrade package_name  # Update specific package
```

## Quality Assurance

### Code Quality Tools

1. Install Pre-commit Hooks
   ```bash
   pre-commit install
   ```

2. Run Linting and Formatting
   ```bash
   # Manual pre-commit check
   pre-commit run --all-files

   # Direct tool usage
   ruff check .    # Linting
   ruff format .   # Formatting
   ```

### Testing

```bash
# Run tests with coverage (either way works)
pytest tests/ -v --cov=app --cov-report=term-missing
# Or using our script
./scripts/test.sh

# View coverage report in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
# or
start htmlcov/index.html     # Windows
```

Test Categories:
- **Unit Tests** (`tests/unit/`): Test components in isolation
- **Integration Tests** (`tests/integration/`): Test API endpoints with test database

## Contributing

1. Create Feature Branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Development Cycle
   - Make your changes
   - Run tests: `./scripts/test.sh`
   - Run quality checks: `pre-commit run --all-files`

3. Submit Pull Request
   - Ensure all tests pass
   - Update documentation if needed
   - Follow existing code style
