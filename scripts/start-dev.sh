#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}


echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"

echo "🚀 Starting server..."
uvicorn app.main:app --reload --host $HOST --port $PORT
