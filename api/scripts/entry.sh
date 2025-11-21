#!/bin/bash
set -e

echo "Starting TBank Queue System..."

echo "Applying database migrations..."
uv run alembic upgrade head

echo "Creating superadmin..."
uv run python -m app.utils.create_first_admin

echo "Starting application..."
exec uv run uvicorn app.main:app --host "${API_HOST}" --port "${API_PORT}" --reload