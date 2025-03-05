#!/usr/bin/env bash

# Exit on error
set -e

cd "$(dirname "$0")/.."
export ENVIRONMENT="test"
export POSTGRES_HOST=${POSTGRES_HOST:-"localhost"}
export POSTGRES_USER=${POSTGRES_USER:-"postgres"}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"postgres"}

echo "🚀 Setting up test environment..."
PGPASSWORD=$POSTGRES_PASSWORD psql -q --no-psqlrc -h $POSTGRES_HOST -U $POSTGRES_USER postgres -c "CREATE DATABASE test_db;"
coverage run -m pytest tests/ -v
coverage report --show-missing
coverage html --title "Receipt Scanner Coverage"
PGPASSWORD=$POSTGRES_PASSWORD psql -q --no-psqlrc -h $POSTGRES_HOST -U $POSTGRES_USER postgres -c "DROP DATABASE IF EXISTS test_db;"
echo "🧹 Cleaning up..."
