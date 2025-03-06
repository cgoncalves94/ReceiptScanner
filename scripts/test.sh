#!/usr/bin/env bash

# Exit on error
set -e

cd "$(dirname "$0")/.."

# Source values directly from .env.test
if [ -f .env.test ]; then
  source .env.test
fi


echo "🚀 Setting up test environment..."

# Setup test database
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS test_db;"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE test_db;"

# Run tests with coverage
coverage run -m pytest tests/ -v

# Generate coverage reports
coverage report --show-missing
coverage html --title "Receipt Scanner Coverage"

# Clean up
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS test_db;"
echo "🧹 Cleaning up..."
