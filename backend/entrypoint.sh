#!/bin/sh
set -e

# Default values
PORT=${PORT:-8000}
GUNICORN_WORKERS=${GUNICORN_WORKERS:-2}
GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-60}

# Normalize list-type env vars (pydantic v2 EnvSettingsSource expects JSON for lists)
# - If set to '*', wrap as JSON array ["*"]
# - If comma-separated, convert to JSON array
if [ -n "${CORS_ORIGINS:-}" ]; then
    case "${CORS_ORIGINS}" in
        \[*\])
            : # already JSON array
            ;;
        "*")
            CORS_ORIGINS='["*"]'
            ;;
        *)
            CORS_ORIGINS=$(python - <<'PY'
import os, json
v=os.environ.get("CORS_ORIGINS","" ).strip()
arr=[s.strip() for s in v.split(",") if s.strip()]
print(json.dumps(arr if arr else ["*"]))
PY
)
            ;;
    esac
    export CORS_ORIGINS
fi

if [ -n "${ALLOWED_HOSTS:-}" ]; then
    case "${ALLOWED_HOSTS}" in
        \[*\])
            : # already JSON array
            ;;
        "*")
            ALLOWED_HOSTS='["*"]'
            ;;
        *)
            ALLOWED_HOSTS=$(python - <<'PY'
import os, json
v=os.environ.get("ALLOWED_HOSTS","" ).strip()
arr=[s.strip() for s in v.split(",") if s.strip()]
print(json.dumps(arr if arr else ["*"]))
PY
)
            ;;
    esac
    export ALLOWED_HOSTS
fi

# Start gunicorn
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:${PORT} \
    --workers ${GUNICORN_WORKERS} \
    --timeout ${GUNICORN_TIMEOUT}
