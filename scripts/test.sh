#!/usr/bin/env bash

# Exit on error
set -e

# Get the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# Change to project root directory
cd "$PROJECT_ROOT"

# Run tests with coverage and generate reports
coverage run -m pytest tests/ -v
coverage report --show-missing
coverage html --title "Receipt Scanner Coverage"
