# AWS → Railway 마이그레이션 요약

## ✅ 완료된 작업

### 1. 데이터베이스 마이그레이션
- **이전**: DynamoDB (NoSQL)
- **이후**: PostgreSQL (SQL)
- **변경사항**:
  - PynamoDB → SQLAlchemy
  - 새로운 모델: `BookSQL`, `AudioChapterSQL`
  - Alembic 마이그레이션 설정
  - 초기 마이그레이션 파일 생성

### 2. 파일 스토리지 마이그레이션
- **이전**: AWS S3
- **이후**: Railway Volumes (로컬 파일 시스템)
- **변경사항**:
  - S3StorageService → LocalStorageService (Railway 환경)
  - `/data` 경로에 마운트
  - 기존 Storage Factory 패턴 유지

### 3. 배포 인프라 변경
- **이전**: Lambda + API Gateway + CloudFront
- **이후**: Railway 컨테이너 + CDN
- **변경사항**:
  - Mangum 제거 (옵션으로 유지)
  - Gunicorn + Uvicorn Workers
  - Railway 자동 HTTPS

### 4. 환경 설정
- **새 설정 클래스**: `RailwaySettings`
- **자동 감지**: `RAILWAY_ENVIRONMENT`, `RAILWAY_PROJECT_ID`
- **환경 변수 예시**: `.env.railway.example`

### 5. 의존성 업데이트
- **제거 (옵션화)**:
  - boto3, botocore, mangum, pynamodb
- **추가**:
  - sqlalchemy, alembic, psycopg2-binary
- **extras 그룹**: `[aws]` (필요시 설치 가능)

## 📁 새로 생성된 파일

### Backend
```
backend/
├── alembic.ini                          # Alembic 설정
├── alembic/
│   ├── env.py                          # 마이그레이션 환경
│   ├── script.py.mako                  # 마이그레이션 템플릿
│   └── versions/
│       └── 001_initial_migration.py    # 초기 마이그레이션
├── app/
│   ├── core/settings/
│   │   └── railway.py                  # Railway 설정
│   └── models/
│       ├── database.py                 # SQLAlchemy 설정
│       ├── book_sql.py                 # Book 모델 (SQL)
│       └── audio_chapter_sql.py        # AudioChapter 모델 (SQL)
```

### Railway 설정
```
├── railway.json                         # Backend Railway 설정
├── railway.toml                         # Backend Railway 설정 (TOML)
├── frontend/railway.json                # Frontend Railway 설정
├── .env.railway.example                 # Backend 환경변수 예시
├── frontend/.env.railway.example        # Frontend 환경변수 예시
```

### 문서
```
├── RAILWAY_DEPLOYMENT.md                # 배포 가이드
└── MIGRATION_SUMMARY.md                 # 이 문서
```

## 🔄 변경된 파일

### Backend
- `pyproject.toml`: 의존성 업데이트, extras 그룹 추가
- `backend/Dockerfile`: PORT 환경변수 지원
- `app/core/settings/factory.py`: RailwaySettings 추가
- `app/services/storage/factory.py`: Railway 환경 지원

### Frontend
- `next.config.js`: Railway 배포 설정 (standalone output)

## ⚠️ 삭제/보관 권장 파일

### AWS 관련 (삭제 가능)
```bash
# SST 설정
rm -rf .sst/
rm sst.config.ts

# Lambda 빌드
rm -rf .lambda-build-host/
rm backend/Dockerfile.lambda
rm .last_image_uri

# AWS 인프라
rm -rf infra/
rm -rf aws-policies/

# AWS 환경 변수
rm .env.production  # AWS ELB URL 포함
```

### 보관 권장 (백업용)
```bash
# 기존 DynamoDB 모델 (참고용)
# backend/app/models/book.py
# backend/app/models/audio_chapter.py

# 기존 AWS 설정
# backend/app/core/settings/production.py
```

## 🚀 배포 체크리스트

### 1. 의존성 설치
```bash
cd backend
poetry install
```

### 2. 데이터베이스 마이그레이션 테스트
```bash
export DATABASE_URL="sqlite:///./test.db"
alembic upgrade head
```

### 3. Railway 배포
```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 생성
railway init

# PostgreSQL 추가 (대시보드)
# Volume 추가 (대시보드)

# 환경변수 설정
railway variables set ENVIRONMENT=railway
railway variables set SIMPLE_AUTH_PASSWORD=강력한비밀번호

# 배포
railway up
```

### 4. 프론트엔드 배포 (Vercel 권장)
```bash
cd frontend
vercel
vercel env add NEXT_PUBLIC_API_URL
# https://your-backend.railway.app 입력
vercel --prod
```

## 📊 비용 비교

### AWS (이전)
- Lambda: ~$5/월
- DynamoDB: ~$5/월
- S3: ~$3/월
- CloudFront: ~$2/월
- **총**: ~$15/월

### Railway (현재)
- PostgreSQL: 포함
- 컨테이너: 포함
- Volumes: 포함
- **Hobby Plan**: $5/월
- **총 예상**: $10-15/월

## 🔧 다음 단계

1. **테스트**:
   - [ ] 로컬 PostgreSQL 테스트
   - [ ] 마이그레이션 검증
   - [ ] API 엔드포인트 테스트

2. **배포**:
   - [ ] Railway 백엔드 배포
   - [ ] Vercel 프론트엔드 배포
   - [ ] 환경변수 설정

3. **데이터 마이그레이션** (기존 데이터 있는 경우):
   - [ ] DynamoDB 데이터 Export
   - [ ] PostgreSQL Import 스크립트 작성
   - [ ] 데이터 검증

4. **모니터링**:
   - [ ] Railway 로그 확인
   - [ ] 헬스 체크 설정
   - [ ] 에러 모니터링

## 💡 주요 개선사항

1. **비용 절감**: AWS $15/월 → Railway $10-15/월
2. **관리 단순화**: 여러 AWS 서비스 → 통합 Railway 플랫폼
3. **배포 간소화**: SST/CDK → Railway CLI/Git Push
4. **개발 경험**: DynamoDB Local → PostgreSQL (표준 SQL)
5. **확장성**: 필요시 AWS extras로 복귀 가능

## 🆘 문제 해결

### 마이그레이션 에러
```bash
# Alembic 상태 확인
alembic current

# 강제 버전 설정
alembic stamp head
```

### Railway 연결 실패
```bash
# 프로젝트 재연결
railway unlink
railway link
```

### 환경 변수 누락
```bash
# 모든 변수 확인
railway variables

# .env.railway.example 참고하여 설정
```
