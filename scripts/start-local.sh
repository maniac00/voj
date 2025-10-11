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

# 2) Prepare backend deps and run Alembic migrations (SQLite / PostgreSQL)
echo "[start-local] Preparing backend dependencies..."
pushd "$ROOT_DIR/backend" >/dev/null
poetry install --no-interaction -E aws || poetry install --no-interaction || true
echo "[start-local] Running DB migrations (alembic upgrade head)..."
(
  export ENVIRONMENT=local
  poetry run alembic upgrade head || true
)
popd >/dev/null

# 3) Start backend (FastAPI) on :8080
echo "[start-local] Starting backend (uvicorn) on :8080..."
pushd "$ROOT_DIR/backend" >/dev/null
(
  export ENVIRONMENT=local
  # Enforce real login flow locally to test static accounts
  export LOCAL_BYPASS_ENABLED=false
  # Explicitly set static accounts for MVP local testing
  export SIMPLE_AUTH_USERNAME=admin
  export SIMPLE_AUTH_PASSWORD=qwer1234
  export SIMPLE_AUTH_APP_USERNAME=dev@example.com
  export SIMPLE_AUTH_APP_PASSWORD=qwer1234
  nohup poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080 \
    >"$STATE_DIR/backend.log" 2>&1 & echo $! >"$STATE_DIR/backend.pid"
)
popd >/dev/null

# 4) Prepare frontend env and start Next dev on :3000 (optional)
if [[ -d "$ROOT_DIR/frontend" ]]; then
  echo "[start-local] Preparing frontend..."
  if [[ ! -f "$ROOT_DIR/frontend/.env.local" ]]; then
    cat > "$ROOT_DIR/frontend/.env.local" <<EOF
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_API_BASE=http://localhost:8080/api/v1
EOF
  else
    # Ensure API envs point to :8080 (idempotent upsert)
    upsert_env() {
      local var_name="$1"
      local var_value="$2"
      local file_path="$3"
      if grep -q "^${var_name}=" "$file_path" >/dev/null 2>&1; then
        # macOS BSD sed (-i '') 또는 GNU sed (-i) 대응
        sed -i '' -e "s|^${var_name}=.*|${var_name}=${var_value}|" "$file_path" 2>/dev/null \
          || sed -i -e "s|^${var_name}=.*|${var_name}=${var_value}|" "$file_path"
      else
        echo "${var_name}=${var_value}" >> "$file_path"
      fi
    }
    upsert_env "NEXT_PUBLIC_API_URL" "http://localhost:8080" "$ROOT_DIR/frontend/.env.local"
    upsert_env "NEXT_PUBLIC_API_BASE" "http://localhost:8080/api/v1" "$ROOT_DIR/frontend/.env.local"
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
echo "- Backend:  http://localhost:8080"
echo "- Frontend: http://localhost:3000 (if started)"
echo "- Auth (MVP static accounts):"
echo "    * Admin: admin / qwer1234"
echo "    * App  : dev@example.com / qwer1234"
echo "Logs: $STATE_DIR/{backend.log,frontend.log}"


