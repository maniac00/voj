#!/bin/bash
set -e

echo "🚀 로컬 개발 환경 설정 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 에러 처리 함수
error_exit() {
    echo -e "${RED}❌ $1${NC}" >&2
    exit 1
}

success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

info_msg() {
    echo -e "${BLUE}📝 $1${NC}"
}

warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. 의존성 확인 및 설치
echo -e "${BLUE}📦 의존성 확인 중...${NC}"

# Node.js 확인
if ! command -v node &> /dev/null; then
    error_exit "Node.js가 설치되지 않았습니다. Node.js 18+ 설치 후 다시 실행해주세요."
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 18 ]; then
    error_exit "Node.js 18+ 버전이 필요합니다. 현재 버전: $NODE_VERSION"
fi
success_msg "Node.js $NODE_VERSION 확인됨"

# Python3 확인
if ! command -v python3 &> /dev/null; then
    error_exit "Python3가 설치되지 않았습니다. Python 3.9+ 설치 후 다시 실행해주세요."
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
success_msg "Python $PYTHON_VERSION 확인됨"

# Docker 확인
if ! command -v docker &> /dev/null; then
    error_exit "Docker가 설치되지 않았습니다. Docker Desktop을 설치해주세요."
fi

# Docker 실행 상태 확인
if ! docker info &> /dev/null; then
    error_exit "Docker가 실행되지 않았습니다. Docker Desktop을 시작해주세요."
fi

DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
success_msg "Docker $DOCKER_VERSION 확인됨"

# 2. Poetry 확인 및 설치
echo -e "${BLUE}📚 Poetry 확인 중...${NC}"

if ! command -v poetry &> /dev/null; then
    warning_msg "Poetry가 설치되지 않았습니다. 설치 중..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Poetry PATH 추가
    export PATH="$HOME/.local/bin:$PATH"
    
    # 현재 세션에서 poetry 사용 가능하도록 설정
    if [ -f "$HOME/.local/bin/poetry" ]; then
        success_msg "Poetry 설치 완료"
    else
        error_exit "Poetry 설치에 실패했습니다. 수동으로 설치해주세요: https://python-poetry.org/docs/#installation"
    fi
else
    POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
    success_msg "Poetry $POETRY_VERSION 확인됨"
fi

# Poetry 설정
echo -e "${BLUE}🐍 Poetry 환경 설정 중...${NC}"

# 가상환경을 프로젝트 내부에 생성하도록 설정
poetry config virtualenvs.in-project true
success_msg "Poetry 가상환경 설정 완료 (.venv 디렉토리 사용)"

# Python 의존성 설치
if [ -f "pyproject.toml" ]; then
    echo -e "${BLUE}📦 Python 패키지 설치 중...${NC}"
    poetry install
    success_msg "Python 패키지 설치 완료"
else
    warning_msg "pyproject.toml 파일이 없습니다"
fi

# 3. Node.js 의존성 설치
echo -e "${BLUE}📦 Node.js 패키지 설치 중...${NC}"
if [ -f "package.json" ]; then
    npm install
    success_msg "Node.js 패키지 설치 완료"
else
    warning_msg "package.json 파일이 없습니다"
fi

# 4. 로컬 스토리지 디렉토리 생성
echo -e "${BLUE}📁 로컬 스토리지 디렉토리 생성 중...${NC}"
mkdir -p storage/audio
success_msg "스토리지 디렉토리 생성 완료: ./storage/audio"

# 5. 환경 변수 파일 생성
echo -e "${BLUE}⚙️  환경 변수 파일 확인 중...${NC}"
if [ ! -f ".env.local" ]; then
    if [ -f "env.local.example" ]; then
        cp env.local.example .env.local
        success_msg "환경 변수 파일 생성 완료: .env.local"
        warning_msg "필요에 따라 .env.local 파일을 수정해주세요"
    else
        warning_msg "env.local.example 파일이 없습니다"
    fi
else
    info_msg ".env.local 파일이 이미 존재합니다"
fi

# 6. DynamoDB Local 설정
echo -e "${BLUE}🗄️  DynamoDB Local 설정 중...${NC}"
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d dynamodb-local
    success_msg "DynamoDB Local 컨테이너 시작됨"
    
    # DynamoDB Local이 준비될 때까지 대기
    echo -e "${BLUE}⏳ DynamoDB Local 준비 대기 중...${NC}"
    sleep 5
    
    # 7. DynamoDB 테이블 생성
    if [ -f "scripts/create-local-tables.py" ]; then
        echo -e "${BLUE}🏗️  DynamoDB 테이블 생성 중...${NC}"
        poetry run python scripts/create-local-tables.py
        success_msg "DynamoDB 테이블 생성 완료"
    else
        warning_msg "scripts/create-local-tables.py 파일이 없습니다"
    fi
else
    warning_msg "docker-compose.yml 파일이 없습니다"
fi

# 8. 개발 서버 시작 안내
echo ""
echo -e "${GREEN}🎉 로컬 개발 환경 설정 완료!${NC}"
echo ""
echo -e "${BLUE}📝 다음 명령어로 개발 서버를 시작하세요:${NC}"
echo ""
echo -e "${YELLOW}  # 백엔드 서버 (FastAPI)${NC}"
echo -e "  poetry run uvicorn backend.main:app --reload --port 8000"
echo ""
echo -e "${YELLOW}  # 프론트엔드 서버 (Next.js)${NC}"
echo -e "  npm run dev:local"
echo ""
echo -e "${BLUE}🔗 접속 URL:${NC}"
echo -e "  - 프론트엔드: http://localhost:3000"
echo -e "  - 백엔드 API: http://localhost:8000"
echo -e "  - DynamoDB Local: http://localhost:8001"
echo ""
echo -e "${BLUE}📋 체크리스트 업데이트를 잊지 마세요!${NC}"
