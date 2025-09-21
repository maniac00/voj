#!/bin/bash
set -euo pipefail

API_URL="${API_URL:-https://api.voj-audiobook.com}"
ENDPOINT="${HEALTH_PATH:-/api/v1/health/detailed}"
EXPECTED_STATUS="${EXPECTED_STATUS:-healthy}"
EXPECTED_ENV="${EXPECTED_ENVIRONMENT:-production}"

FULL_URL="${API_URL%/}${ENDPOINT}"

echo "요청 URL: ${FULL_URL}" >&2

RESPONSE=$(curl -fsSL --max-time 10 "${FULL_URL}") || {
  echo "요청 실패" >&2
  exit 1
}

echo "응답: ${RESPONSE}" >&2

python3 - "$RESPONSE" "$EXPECTED_STATUS" "$EXPECTED_ENV" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except json.JSONDecodeError:
    print("JSON 파싱 실패", file=sys.stderr)
    sys.exit(2)

expected_status = sys.argv[2]
expected_env = sys.argv[3]

status = payload.get("status")
environment = payload.get("environment")

if status != expected_status:
    print(f"상태 불일치: {status} != {expected_status}", file=sys.stderr)
    sys.exit(3)
if environment != expected_env:
    print(f"환경 불일치: {environment} != {expected_env}", file=sys.stderr)
    sys.exit(4)

print("OK")
PY
