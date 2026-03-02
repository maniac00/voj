#!/usr/bin/env bash
set -euo pipefail

echo "=== Backend (Railway) 배포 ==="
echo ""
echo "Railway는 main 브랜치 푸시 시 자동 배포됩니다."
echo ""
echo "수동 배포가 필요한 경우:"
echo "  cd backend && railway up"
echo ""
echo "프로덕션 URL: https://voj-production.up.railway.app"
echo "헬스체크:     https://voj-production.up.railway.app/health"
echo ""

read -p "헬스체크를 실행하시겠습니까? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "헬스체크 요청 중..."
  curl -s -o /dev/null -w "HTTP %{http_code} (%{time_total}s)\n" \
    https://voj-production.up.railway.app/health
fi
