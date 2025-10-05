#!/bin/bash
# VOJ Audiobooks Backend - 로컬 개발 서버 실행 스크립트

set -e

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 메시지 함수
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}
info_msg() {
    echo -e "${BLUE}📋 $1${NC}"
}
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}
error_exit() {
    echo -e "${RED}❌ $1${NC}" >&2
    exit 1
}

# 현재 디렉토리 확인
if [[ ! -f "app/main.py" ]]; then
    error_exit "backend 디렉토리에서 실행해주세요"
fi

info_msg "VOJ Audiobooks Backend - 로컬 개발 서버 시작"

# 환경 변수 설정
export ENVIRONMENT=local

# Poetry 가상환경 확인
if ! command -v poetry &> /dev/null; then
    error_exit "Poetry가 설치되지 않았습니다. 'brew install poetry'로 설치해주세요"
fi

# 의존성 설치 확인
info_msg "의존성 확인 중..."
poetry install

# 로컬 스토리지 디렉토리 생성
info_msg "로컬 스토리지 디렉토리 생성 중..."
mkdir -p storage/{uploads,media,books}

# DynamoDB Local 상태 확인
info_msg "DynamoDB Local 연결 확인 중..."
if ! curl -s http://localhost:8001 > /dev/null 2>&1; then
    warning_msg "DynamoDB Local이 실행되지 않았습니다"
    info_msg "다음 명령어로 DynamoDB Local을 시작해주세요:"
    echo "  cd .. && docker-compose up -d dynamodb-local"
fi

# FastAPI 서버 시작
success_msg "FastAPI 로컬 개발 서버 시작 중..."
info_msg "서버 주소: http://localhost:8080"
info_msg "API 문서: http://localhost:8080/docs"
info_msg "종료하려면 Ctrl+C를 누르세요"

poetry run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    --log-level info
