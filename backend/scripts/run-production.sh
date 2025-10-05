#!/bin/bash
# VOJ Audiobooks Backend - 프로덕션 서버 실행 스크립트

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

info_msg "VOJ Audiobooks Backend - 프로덕션 서버 시작"

# 환경 변수 설정
export ENVIRONMENT=production

# 필수 환경 변수 확인
required_vars=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "COGNITO_USER_POOL_ID"
    "COGNITO_CLIENT_ID"
    "COGNITO_CLIENT_SECRET"
)

for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        error_exit "필수 환경 변수가 설정되지 않았습니다: $var"
    fi
done

# Poetry 가상환경 확인
if ! command -v poetry &> /dev/null; then
    error_exit "Poetry가 설치되지 않았습니다"
fi

# 의존성 설치 (프로덕션용)
info_msg "프로덕션 의존성 설치 중..."
poetry install --without dev

# AWS 연결 확인
info_msg "AWS 서비스 연결 확인 중..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    error_exit "AWS 인증이 설정되지 않았습니다"
fi

# DynamoDB 테이블 존재 확인
info_msg "DynamoDB 테이블 확인 중..."
if ! aws dynamodb describe-table --table-name voj-books-prod --region ap-northeast-2 > /dev/null 2>&1; then
    warning_msg "voj-books-prod 테이블이 존재하지 않습니다"
fi

# 임시 디렉토리 생성 (Lambda/컨테이너 환경용)
info_msg "임시 디렉토리 생성 중..."
mkdir -p /tmp/{uploads,media,books}

# FastAPI 프로덕션 서버 시작
success_msg "FastAPI 프로덕션 서버 시작 중..."
info_msg "환경: Production"
info_msg "포트: 8080"

poetry run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4 \
    --log-level info \
    --access-log
