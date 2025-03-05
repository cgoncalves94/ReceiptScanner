#!/usr/bin/env bash

    # Exit if any command fails
    set -e

    # Set project root and add to Python path
    SCRIPT_DIR=$(dirname "$0")
    PROJECT_ROOT="$SCRIPT_DIR/.."
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # Set default app module
    DEFAULT_MODULE_NAME=app.main
    MODULE_NAME=${MODULE_NAME:-$DEFAULT_MODULE_NAME}
    VARIABLE_NAME=${VARIABLE_NAME:-app}
    export APP_MODULE=${APP_MODULE:-"$MODULE_NAME:$VARIABLE_NAME"}

    # Set host, port, and log level
    HOST=${HOST:-0.0.0.0}
    PORT=${PORT:-8000}
    LOG_LEVEL=${LOG_LEVEL:-debug}

    echo "Running database migrations..."
    alembic upgrade head

    echo "Starting application server..."
    # Start Uvicorn with live reload
    exec uvicorn --reload --proxy-headers --host $HOST --port $PORT --log-level $LOG_LEVEL "$APP_MODULE"
