#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Frontend (Vercel) 프로덕션 배포 ==="
cd "$PROJECT_ROOT/frontend"

npx vercel --prod --yes

echo ""
echo "=== 배포 완료 ==="
echo "URL: https://voj-admin.vercel.app"
