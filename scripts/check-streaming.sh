#!/bin/bash
set -euo pipefail

SIGNED_URL="${1:-${SIGNED_URL:-}}"
if [ -z "${SIGNED_URL}" ]; then
  echo "사용 방법: SIGNED_URL=<url> ./scripts/check-streaming.sh" >&2
  exit 1
fi

RANGE_HEADER="bytes=0-127"

echo "Range 테스트 (0-127 바이트)" >&2
STATUS=$(curl -s -o /tmp/stream_check.bin -w "%{http_code}" -H "Range: ${RANGE_HEADER}" "${SIGNED_URL}") || {
  echo "요청 실패" >&2
  exit 2
}

echo "HTTP 상태: ${STATUS}" >&2
if [ "${STATUS}" != "206" ]; then
  echo "경고: 206 Partial Content가 아님" >&2
fi

CONTENT_RANGE=$(curl -sI -H "Range: ${RANGE_HEADER}" "${SIGNED_URL}" | grep -i "^Content-Range") || true
if [ -n "${CONTENT_RANGE}" ]; then
  echo "Content-Range: ${CONTENT_RANGE}" >&2
else
  echo "Content-Range 헤더 없음" >&2
fi

BYTES=$(wc -c </tmp/stream_check.bin | tr -d ' ')
rm -f /tmp/stream_check.bin

echo "수신 바이트: ${BYTES}" >&2
if [ "${BYTES}" -lt 1 ]; then
  echo "경고: 응답 바이트가 0" >&2
  exit 3
fi

echo "OK"
