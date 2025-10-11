#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
STATE_DIR="$ROOT_DIR/.local-dev"

echo "[stop-local] Repo: $ROOT_DIR"

# Helpers
kill_safely() {
  local pid="$1"
  if [[ -z "$pid" ]]; then return; fi
  if ! ps -p "$pid" >/dev/null 2>&1; then return; fi
  echo "[stop-local] Sending TERM to pid $pid"
  kill "$pid" || true
  sleep 1
  if ps -p "$pid" >/dev/null 2>&1; then
    echo "[stop-local] Sending TERM to process group -$pid"
    kill -TERM -"$pid" || true
    sleep 1
  fi
  if ps -p "$pid" >/dev/null 2>&1; then
    echo "[stop-local] Sending KILL to pid $pid and group -$pid"
    kill -9 "$pid" || true
    kill -9 -"$pid" || true
  fi
}

kill_by_port() {
  local port="$1"
  echo "[stop-local] Ensuring port $port is free..."
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -ti tcp:"$port" || true)
    if [[ -n "$pids" ]]; then
      echo "[stop-local] Killing processes on :$port -> $pids"
      kill $pids || true
      sleep 1
      local left
      left=$(lsof -ti tcp:"$port" || true)
      if [[ -n "$left" ]]; then
        echo "[stop-local] Force killing processes on :$port -> $left"
        kill -9 $left || true
      fi
    fi
  else
    if command -v netstat >/dev/null 2>&1; then
      local pid
      pid=$(netstat -anv | awk '/\.'"$port"' .*LISTEN/ {print $9}' | head -n1 || true)
      if [[ -n "$pid" ]]; then
        echo "[stop-local] Killing process on :$port -> $pid"
        kill "$pid" || true
        sleep 1
        if netstat -anv | grep -q "\.$port .*LISTEN"; then
          echo "[stop-local] Force killing process on :$port -> $pid"
          kill -9 "$pid" || true
        fi
      fi
    fi
  fi
}

# 1) Stop frontend if running
if [[ -f "$STATE_DIR/frontend.pid" ]]; then
  PID=$(cat "$STATE_DIR/frontend.pid" || true)
  if [[ -n "${PID}" ]] && ps -p "$PID" >/dev/null 2>&1; then
    echo "[stop-local] Stopping frontend (pid $PID)..."
    kill_safely "$PID"
  fi
  rm -f "$STATE_DIR/frontend.pid"
fi

# 2) Stop backend if running
if [[ -f "$STATE_DIR/backend.pid" ]]; then
  PID=$(cat "$STATE_DIR/backend.pid" || true)
  if [[ -n "${PID}" ]] && ps -p "$PID" >/dev/null 2>&1; then
    echo "[stop-local] Stopping backend (pid $PID)..."
    kill_safely "$PID"
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

echo "[stop-local] Primary PID-based stop attempted."

# 4) Unset local auth overrides to avoid polluting shell sessions
unset SIMPLE_AUTH_USERNAME SIMPLE_AUTH_PASSWORD SIMPLE_AUTH_APP_USERNAME SIMPLE_AUTH_APP_PASSWORD LOCAL_BYPASS_ENABLED || true


# Extra safety: kill by known process names if still running
if command -v pkill >/dev/null 2>&1; then
  echo "[stop-local] Attempting pkill for uvicorn/next dev..."
  pkill -f "uvicorn app.main:app --host 0.0.0.0 --port 8080" || true
  pkill -f "next dev" || true
fi

# Ensure ports are freed (backend :8080, frontend :3000)
kill_by_port 8080
kill_by_port 3000

echo "[stop-local] Done. Logs remain in $STATE_DIR."



