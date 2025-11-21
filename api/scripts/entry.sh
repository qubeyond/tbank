#!/bin/bash
set -e

echo "Starting TBank Queue System..."

uv run alembic upgrade head

exec uv run uvicorn app.main:app --host "${API_HOST}" --port "${API_PORT}" --reload