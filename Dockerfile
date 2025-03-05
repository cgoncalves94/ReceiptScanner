FROM python:3.12-slim-bookworm

# Install system dependencies including OpenCV requirements
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

WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv

# Environment setup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONPATH=/app

# Copy project files and install
COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY scripts ./scripts
COPY migrations ./migrations
RUN uv pip install --system .[all] && \
    useradd -m -d /app -s /bin/bash app && \
    chown -R app:app /app && \
    chmod +x /app/scripts/start-dev.sh

USER app

CMD ["/app/scripts/start-dev.sh"]
