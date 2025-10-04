#!/bin/bash

# Railway 배포 자동화 스크립트
# 사용법: ./scripts/railway-setup.sh

set -e

echo "🚀 Railway 프로젝트 설정 시작..."

# 프로젝트 ID
PROJECT_ID="ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29"

echo ""
echo "📋 필요한 설정:"
echo "1. PostgreSQL 데이터베이스"
echo "2. Volume (파일 스토리지)"
echo "3. 환경변수"
echo ""

# Railway CLI 확인
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI가 설치되지 않았습니다."
    echo "설치: npm install -g @railway/cli"
    exit 1
fi

# 로그인 확인
echo "🔐 Railway 로그인 확인..."
if ! railway whoami &> /dev/null; then
    echo "❌ Railway 로그인이 필요합니다."
    echo "실행: railway login"
    exit 1
fi

echo "✅ 로그인 성공"

# 프로젝트 연결
echo ""
echo "🔗 프로젝트 연결 중..."
cd backend
railway link $PROJECT_ID || true

echo ""
echo "⚠️  Railway 대시보드에서 수동으로 추가해야 할 항목:"
echo ""
echo "1️⃣ PostgreSQL 추가:"
echo "   https://railway.com/project/$PROJECT_ID/services"
echo "   → New → Database → PostgreSQL"
echo ""
echo "2️⃣ Volume 추가:"
echo "   → New → Volume"
echo "   → Name: voj-storage"
echo "   → Mount Path: /data"
echo ""
echo "3️⃣ 환경변수 설정 (Variables 탭):"
echo "   ENVIRONMENT=railway"
echo "   PORT=8000"
echo "   SIMPLE_AUTH_USERNAME=admin"
echo "   SIMPLE_AUTH_PASSWORD=강력한_비밀번호"
echo "   CORS_ORIGINS=*"
echo "   LOG_LEVEL=INFO"
echo ""

read -p "위 설정을 완료했나요? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "설정 완료 후 다시 실행해주세요."
    exit 0
fi

# 배포
echo ""
echo "📦 배포 시작..."
railway up

echo ""
echo "✅ 배포 완료!"
echo ""
echo "🔍 배포 상태 확인:"
echo "   railway logs -f"
echo ""
echo "🌐 프로젝트 URL:"
echo "   https://railway.com/project/$PROJECT_ID"
