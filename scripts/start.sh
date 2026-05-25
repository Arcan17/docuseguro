#!/usr/bin/env bash
set -e

# Railway provides DATABASE_URL as postgresql://, SQLAlchemy async needs postgresql+asyncpg://
if [[ -n "$DATABASE_URL" ]]; then
    export DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+asyncpg://}"
    echo "[start] DATABASE_URL driver rewritten to asyncpg"
fi

# Create tables
echo "[start] Creating tables..."
python -c "
import asyncio
from app.models.database import create_tables
asyncio.run(create_tables())
print('[start] Tables ready.')
"

# Seed demo documents (skips if already seeded)
echo "[start] Checking demo data..."
python scripts/seed_demo.py

# Start server — Railway injects PORT, default 8000
PORT="${PORT:-8000}"
echo "[start] Starting uvicorn on port $PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1
