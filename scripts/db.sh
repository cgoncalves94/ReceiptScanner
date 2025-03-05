#!/usr/bin/env bash

# Exit on error
set -e

# Set project root
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"
