#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
STATE_DIR="$ROOT_DIR/.local-dev"

echo "[stop-local] Repo: $ROOT_DIR"

# 1) Stop frontend if running
if [[ -f "$STATE_DIR/frontend.pid" ]]; then
  PID=$(cat "$STATE_DIR/frontend.pid" || true)
  if [[ -n "${PID}" ]] && ps -p "$PID" >/dev/null 2>&1; then
    echo "[stop-local] Stopping frontend (pid $PID)..."
    kill "$PID" || true
  fi
  rm -f "$STATE_DIR/frontend.pid"
fi

# 2) Stop backend if running
if [[ -f "$STATE_DIR/backend.pid" ]]; then
  PID=$(cat "$STATE_DIR/backend.pid" || true)
  if [[ -n "${PID}" ]] && ps -p "$PID" >/dev/null 2>&1; then
    echo "[stop-local] Stopping backend (pid $PID)..."
    kill "$PID" || true
  fi
  rm -f "$STATE_DIR/backend.pid"
fi

# 3) Stop DynamoDB Local container
echo "[stop-local] Stopping DynamoDB Local..."
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose -f "$ROOT_DIR/docker-compose.yml" stop dynamodb-local || true
else
  docker-compose -f "$ROOT_DIR/docker-compose.yml" stop dynamodb-local || true
fi

echo "[stop-local] Done. Logs remain in $STATE_DIR."


