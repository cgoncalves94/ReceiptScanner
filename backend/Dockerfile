FROM python:3.14-slim-bookworm

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    gcc \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpq-dev \
    libssl-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONPATH=/app

# Copy project files
COPY pyproject.toml uv.lock alembic.ini ./
COPY app ./app
COPY migrations ./migrations

# Install dependencies
RUN uv sync --frozen --no-dev

# Create uploads directory and non-root user
RUN mkdir -p /app/uploads && \
    useradd -m -d /app -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
