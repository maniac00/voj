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

# 4) Ensure port 3000 is free (Next dev default)
echo "[stop-local] Ensuring port 3000 is free..."
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -ti tcp:3000 || true)
  if [[ -n "${PIDS}" ]]; then
    echo "[stop-local] Killing processes on :3000 -> ${PIDS}"
    kill ${PIDS} || true
    sleep 1
    LEFT=$(lsof -ti tcp:3000 || true)
    if [[ -n "${LEFT}" ]]; then
      echo "[stop-local] Force killing processes on :3000 -> ${LEFT}"
      kill -9 ${LEFT} || true
    fi
  fi
else
  # Fallback using netstat for systems without lsof
  if command -v netstat >/dev/null 2>&1; then
    PID=$(netstat -anv | awk '/\.3000 .*LISTEN/ {print $9}' | head -n1 || true)
    if [[ -n "${PID}" ]]; then
      echo "[stop-local] Killing process on :3000 -> ${PID}"
      kill ${PID} || true
      sleep 1
      if netstat -anv | grep -q "\.3000 .*LISTEN"; then
        echo "[stop-local] Force killing process on :3000 -> ${PID}"
        kill -9 ${PID} || true
      fi
    fi
  fi
fi



