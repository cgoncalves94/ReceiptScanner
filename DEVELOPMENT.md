# Development Guide for Receipt Scanner API

This guide provides practical instructions for setting up, running, and contributing to the Receipt Scanner API project.

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- UV package manager
- Google Gemini API key

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/receipt-scanner.git
cd receipt-scanner
```

### 2. Start Database

```bash
# Start PostgreSQL database
docker compose up db -d
```

### 3. Install Dependencies

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# Install all dependencies
uv pip install -e .

# Or install with development dependencies
uv pip install -e ".[dev]"
```

### 4. Setup Environment

```bash
cp .env.example .env
# Edit .env with your configurations, especially the Gemini API key
```

### 5. Run Application

```bash
uvicorn src.main:app --reload
```

The API will be available at http://localhost:8000

## Package Management with UV

UV is our recommended package manager for its speed and reliability.

### Installing Packages

```bash
# Add a new package
uv pip install package_name

# Install the package and add it to pyproject.toml
uv add package_name

# Add a development dependency
uv add --dev package_name
```

### Managing Dependencies

```bash
# View installed packages
uv pip list

# Check for outdated packages
uv pip list --outdated
```

## Docker Development

### Building and Running

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f
```

## Code Quality Tools

### Pre-commit Hooks

To ensure code quality and consistency:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Linting and Formatting

The project uses Ruff for linting and formatting:

```bash
# Run linter
ruff check .

# Run formatter
ruff format .
```

## Contributing

1. Create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests and pre-commit hooks
   ```bash
   pre-commit run --all-files
   pytest
   ```

4. Submit a pull request
