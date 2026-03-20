#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Running database migrations..."
alembic upgrade head
echo "[entrypoint] Migration done."

echo "[entrypoint] Starting app: $*"
exec "$@"
