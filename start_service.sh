#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Installing dependencies ==="
poetry install

echo "=== Changing directory ==="
cd "$1"
pwd

echo "=== Starting the microservice ==="
poetry run python "$2"