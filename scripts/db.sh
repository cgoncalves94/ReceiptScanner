#!/usr/bin/env bash

# Exit on error
set -e

# Set project root
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

# Run migrations
alembic upgrade head
