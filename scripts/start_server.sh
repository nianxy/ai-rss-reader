#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${ENV_NAME:-rss-reader}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:---reload}"

cd "$(dirname "$0")/.."

# db migration
alembic upgrade head

# start server
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}" ${RELOAD}
