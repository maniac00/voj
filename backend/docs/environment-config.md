# VOJ Audiobooks Backend - 환경별 설정 가이드

## 개요

VOJ Audiobooks Backend는 환경별로 다른 설정을 사용하여 로컬 개발과 프로덕션 배포를 지원합니다.

## 환경 구분

### 1. 로컬 개발 환경 (local)

**특징:**
- DynamoDB Local 사용 (Docker)
- 로컬 파일 시스템 스토리지
- 개발용 CORS 설정 (관대한 정책)
- 상세한 디버그 로그
- API 문서 활성화

**실행 방법:**
```bash
cd backend
./scripts/run-local.sh
```

**주요 설정:**
- `ENVIRONMENT=local`
- `DYNAMODB_ENDPOINT_URL=http://localhost:8001`
- `LOG_LEVEL=DEBUG`
- API 문서: http://localhost:8000/docs

### 2. 프로덕션 환경 (production)

**특징:**
- AWS DynamoDB 사용
- AWS S3 스토리지
- CloudFront Signed URL
- 엄격한 CORS 설정
- 프로덕션 로그 레벨
- API 문서 비활성화

**실행 방법:**
```bash
cd backend
export ENVIRONMENT=production
./scripts/run-production.sh
```

**주요 설정:**
- `ENVIRONMENT=production`
- `DYNAMODB_ENDPOINT_URL=None` (AWS DynamoDB)
- `LOG_LEVEL=INFO`
- API 문서: 비활성화

## 설정 클래스 구조

```
app/core/settings/
├── __init__.py
├── base.py          # 공통 기본 설정
├── local.py         # 로컬 개발 환경 설정
├── production.py    # 프로덕션 환경 설정
└── factory.py       # 설정 팩토리 (환경별 설정 선택)
```

## 환경별 주요 차이점

| 설정 항목 | 로컬 | 프로덕션 |
|-----------|------|----------|
| DynamoDB | Local (Docker) | AWS DynamoDB |
| 스토리지 | 로컬 파일 시스템 | AWS S3 |
| CDN | 없음 | CloudFront |
| 테이블 이름 | `*-local` | `*-prod` |
| CORS | 관대한 설정 | 엄격한 설정 |
| 로그 레벨 | DEBUG | INFO |
| API 문서 | 활성화 | 비활성화 |
| FFmpeg 경로 | Homebrew 경로 | Lambda Layer 경로 |

## 환경 변수

### 공통 환경 변수
- `ENVIRONMENT`: 환경 구분 (local/production)
- `AWS_REGION`: AWS 리전 (기본: ap-northeast-2)

### Cognito 관련 환경 변수
- `COGNITO_USER_POOL_ID`: Cognito 사용자 풀 ID (로컬은 비워두면 인증 바이패스)
- `COGNITO_CLIENT_ID`: Cognito 클라이언트 ID
- `COGNITO_CLIENT_SECRET`: Cognito 클라이언트 시크릿 (프로덕션은 Secrets Manager 권장)
- `COGNITO_DOMAIN`: Cognito 도메인(Hosted UI 사용 시)

### 로컬 인증 바이패스 환경 변수
- `LOCAL_BYPASS_ENABLED`: true/false, Authorization 헤더 없을 때 BYPASS 허용 여부
- `LOCAL_BYPASS_SUB`, `LOCAL_BYPASS_EMAIL`, `LOCAL_BYPASS_USERNAME`, `LOCAL_BYPASS_SCOPE`, `LOCAL_BYPASS_GROUPS`

## 설정 확인 방법

### 1. 기본 상태 확인
```bash
curl http://localhost:8000/
```

### 2. 상세 헬스 체크
```bash
curl http://localhost:8000/api/v1/health/detailed
```

### 3. 환경별 설정 확인
- 로컬: `environment: "local"`
- 프로덕션: `environment: "production"`

## 문제 해결

### DynamoDB Local 연결 오류
```bash
# DynamoDB Local 시작
cd .. && docker-compose up -d dynamodb-local

# 연결 확인
curl http://localhost:8001
```

### Poetry 환경 문제
```bash
# Poetry 가상환경 재생성
poetry env remove --all
poetry install
```

### 환경 변수 확인
```bash
# 현재 환경 확인
echo $ENVIRONMENT

# 환경 변수 설정
export ENVIRONMENT=local  # 또는 production
```

