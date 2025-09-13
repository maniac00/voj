#!/usr/bin/env bash
set -euo pipefail

# Determine repo root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
STATE_DIR="$ROOT_DIR/.local-dev"
mkdir -p "$STATE_DIR"

echo "[start-local] Repo: $ROOT_DIR"

# 1) Ensure .env.local exists (backend/env)
if [[ ! -f "$ROOT_DIR/.env.local" ]]; then
  echo "[start-local] Creating .env.local from example..."
  cp "$ROOT_DIR/env.local.example" "$ROOT_DIR/.env.local"
fi

# 2) Start DynamoDB Local via docker compose
echo "[start-local] Starting DynamoDB Local..."
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose -f "$ROOT_DIR/docker-compose.yml" up -d dynamodb-local
else
  docker-compose -f "$ROOT_DIR/docker-compose.yml" up -d dynamodb-local
fi

# 3) Wait for host port to accept connections (prefer this over container health)
echo "[start-local] Waiting for DynamoDB Local on host port 8001..."
for i in {1..90}; do
  if command -v nc >/dev/null 2>&1; then
    if nc -z localhost 8001 >/dev/null 2>&1; then
      echo "[start-local] Port 8001 reachable."
      break
    fi
  else
    if curl -sSf "http://localhost:8001" >/dev/null 2>&1; then
      echo "[start-local] Port 8001 reachable."
      break
    fi
  fi
  sleep 1
  if [[ $i -eq 90 ]]; then
    echo "[start-local] ERROR: DynamoDB Local not reachable on port 8001 in time." >&2
    exit 1
  fi
done

# 4) Create local tables and sample data
echo "[start-local] Creating local tables..."
pushd "$ROOT_DIR" >/dev/null
poetry run python scripts/create-local-tables.py || true
popd >/dev/null

# 5) Start backend (FastAPI) on :8000
echo "[start-local] Starting backend (uvicorn) on :8000..."
pushd "$ROOT_DIR/backend" >/dev/null
(
  export ENVIRONMENT=local
  nohup poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    >"$STATE_DIR/backend.log" 2>&1 & echo $! >"$STATE_DIR/backend.pid"
)
popd >/dev/null

# 6) Prepare frontend env and start Next dev on :3000 (optional)
if [[ -d "$ROOT_DIR/frontend" ]]; then
  echo "[start-local] Preparing frontend..."
  if [[ ! -f "$ROOT_DIR/frontend/.env.local" ]]; then
    cat > "$ROOT_DIR/frontend/.env.local" <<EOF
NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
EOF
  fi

  if command -v node >/dev/null 2>&1; then
    echo "[start-local] Starting frontend (next dev) on :3000..."
    pushd "$ROOT_DIR/frontend" >/dev/null
    # Install deps if node_modules missing (allow legacy peer deps for React 19 conflicts)
    if [[ ! -d node_modules ]]; then
      npm install --no-fund --no-audit --legacy-peer-deps || true
    fi
    (nohup npm run dev >"$STATE_DIR/frontend.log" 2>&1 & echo $! >"$STATE_DIR/frontend.pid")
    popd >/dev/null
  else
    echo "[start-local] WARN: Node.js not found; skipping frontend start."
  fi
else
  echo "[start-local] NOTE: frontend directory not found; skipping frontend."
fi

echo "[start-local] Local environment started."
echo "- Backend:  http://localhost:8000"
echo "- Frontend: http://localhost:3000 (if started)"
echo "Logs: $STATE_DIR/{backend.log,frontend.log}"


