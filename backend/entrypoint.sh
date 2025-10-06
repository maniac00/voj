#!/bin/sh
set -e

# Default values
PORT=${PORT:-8080}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-60}

# Normalize list-type env vars (pydantic v2 EnvSettingsSource expects JSON for lists)
# - If env var is present but empty, default to ["*"] to avoid JSONDecodeError
# - If set to '*', wrap as JSON array ["*"]
# - If comma-separated, convert to JSON array

# Always coerce to valid JSON arrays to avoid pydantic JSONDecodeError
case "${CORS_ORIGINS:-}" in
    \[*\])
        :
        ;;
    ""|"*")
        CORS_ORIGINS='["*"]'
        ;;
    *','*)
        CORS_ORIGINS=$(python - <<'PY'
import os, json
v=os.environ.get("CORS_ORIGINS","" ).strip()
arr=[s.strip() for s in v.split(",") if s.strip()]
print(json.dumps(arr if arr else ["*"]))
PY
)
        ;;
    *)
        CORS_ORIGINS=$(python - <<'PY'
import os, json
v=os.environ.get("CORS_ORIGINS","" ).strip()
print(json.dumps([v] if v else ["*"]))
PY
)
        ;;
esac
export CORS_ORIGINS

case "${ALLOWED_HOSTS:-}" in
    \[*\])
        :
        ;;
    ""|"*")
        ALLOWED_HOSTS='["*"]'
        ;;
    *','*)
        ALLOWED_HOSTS=$(python - <<'PY'
import os, json
v=os.environ.get("ALLOWED_HOSTS","" ).strip()
arr=[s.strip() for s in v.split(",") if s.strip()]
print(json.dumps(arr if arr else ["*"]))
PY
)
        ;;
    *)
        ALLOWED_HOSTS=$(python - <<'PY'
import os, json
v=os.environ.get("ALLOWED_HOSTS","" ).strip()
print(json.dumps([v] if v else ["*"]))
PY
)
        ;;
esac
export ALLOWED_HOSTS

# Safety: avoid pydantic JSON parsing from env for list fields; use code defaults
unset CORS_ORIGINS || true
unset ALLOWED_HOSTS || true

# Run DB migrations (idempotent)
echo "[entrypoint] Running database migrations (alembic upgrade head)"
if command -v poetry >/dev/null 2>&1; then
    poetry run alembic upgrade head || true
elif command -v alembic >/dev/null 2>&1; then
    alembic upgrade head || true
elif [ -x "/app/.venv/bin/alembic" ]; then
    /app/.venv/bin/alembic upgrade head || true
else
    echo "[entrypoint] WARNING: alembic not found in PATH; skipping migrations"
fi

# Start gunicorn
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:${PORT} \
    --workers ${GUNICORN_WORKERS} \
    --timeout ${GUNICORN_TIMEOUT}
