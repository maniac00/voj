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

# Start gunicorn
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:${PORT} \
    --workers ${GUNICORN_WORKERS} \
    --timeout ${GUNICORN_TIMEOUT}
