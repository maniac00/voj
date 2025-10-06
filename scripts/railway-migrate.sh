#!/bin/bash

# Railway 데이터베이스 마이그레이션 스크립트
# 사용법: ./scripts/railway-migrate.sh

set -e

echo "🗄️  Railway 데이터베이스 마이그레이션"
echo ""

# Railway 대시보드에서 DATABASE_URL 복사 필요
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL 환경변수가 설정되지 않았습니다."
    echo ""
    echo "📋 Railway 대시보드에서 DATABASE_URL 복사:"
    echo "1. https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29 접속"
    echo "2. PostgreSQL 서비스 클릭"
    echo "3. 'Variables' 탭 → DATABASE_URL 값 복사"
    echo "4. 다음 명령어로 실행:"
    echo ""
    echo "   export DATABASE_URL='복사한_URL'"
    echo "   ./scripts/railway-migrate.sh"
    echo ""
    exit 1
fi

echo "✅ DATABASE_URL 확인됨"
echo ""

# backend 디렉토리로 이동
cd backend

# PostgreSQL URL 형식 확인 및 수정
if [[ $DATABASE_URL == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
    echo "🔄 URL 형식 수정: postgres:// → postgresql://"
fi

echo "🔍 현재 마이그레이션 상태 확인..."
if command -v poetry >/dev/null 2>&1; then
  poetry run alembic current || echo "마이그레이션 히스토리 없음"
else
  alembic current || echo "마이그레이션 히스토리 없음"
fi

echo ""
echo "⬆️  마이그레이션 실행..."
if command -v poetry >/dev/null 2>&1; then
  poetry run alembic upgrade head
else
  alembic upgrade head
fi

echo ""
echo "✅ 마이그레이션 완료!"
echo ""
echo "🔍 최종 상태:"
if command -v poetry >/dev/null 2>&1; then
  poetry run alembic current
else
  alembic current
fi

echo ""
echo "📊 테이블 확인 (psql 사용):"
echo "   psql \$DATABASE_URL -c '\\dt'"
