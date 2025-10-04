# VOJ Audiobooks - Railway 배포 가이드

Railway를 사용한 저비용 MVP 프로덕션 배포 가이드입니다.

## 📋 사전 준비

### 1. Railway 계정 생성
- [Railway](https://railway.app/) 회원가입
- GitHub 계정 연동

### 2. Railway CLI 설치
```bash
npm install -g @railway/cli
railway login
```

## 🚀 배포 단계

### Step 1: 프로젝트 생성

```bash
# Railway 프로젝트 생성
railway init

# 프로젝트 연결
railway link
```

### Step 2: PostgreSQL 데이터베이스 추가

1. Railway 대시보드에서 **New** → **Database** → **PostgreSQL** 선택
2. 자동으로 `DATABASE_URL` 환경변수가 생성됨

### Step 3: Railway Volumes 추가 (파일 스토리지)

1. Railway 대시보드에서 **New** → **Volume** 선택
2. Volume 이름: `voj-storage`
3. Mount Path: `/data`
4. 자동으로 `RAILWAY_VOLUME_MOUNT_PATH=/data` 환경변수 생성됨

### Step 4: 백엔드 배포

#### 4-1. 의존성 업데이트
```bash
cd backend
poetry install
poetry lock
```

#### 4-2. 환경변수 설정
Railway 대시보드의 **Variables** 섹션에서 설정:

```bash
# 필수 환경변수
ENVIRONMENT=railway
PORT=8000

# 인증 (보안 강화 필수!)
SIMPLE_AUTH_USERNAME=admin
SIMPLE_AUTH_PASSWORD=강력한_비밀번호_여기에

# CORS (프론트엔드 URL 추가)
CORS_ORIGINS=https://your-frontend.railway.app,https://your-frontend.vercel.app
ALLOWED_HOSTS=*

# 로깅
LOG_LEVEL=INFO
```

#### 4-3. 데이터베이스 마이그레이션
```bash
# 로컬에서 마이그레이션 테스트
export DATABASE_URL="postgresql://..."  # Railway에서 복사
cd backend
alembic upgrade head
```

#### 4-4. 백엔드 배포
```bash
# railway.json 설정 확인
cat railway.json

# 배포 실행
railway up
```

### Step 5: 프론트엔드 배포

#### 옵션 A: Railway로 배포

```bash
cd frontend

# Railway 프로젝트 새로 생성
railway init

# 환경변수 설정
railway variables set NEXT_PUBLIC_API_URL=https://your-backend.railway.app
railway variables set NEXT_PUBLIC_API_BASE=https://your-backend.railway.app/api/v1

# 배포
railway up
```

#### 옵션 B: Vercel로 배포 (권장)

```bash
cd frontend

# Vercel CLI 설치 (없으면)
npm install -g vercel

# 배포
vercel

# 환경변수 설정
vercel env add NEXT_PUBLIC_API_URL
# 입력: https://your-backend.railway.app

vercel env add NEXT_PUBLIC_API_BASE
# 입력: https://your-backend.railway.app/api/v1

# 프로덕션 배포
vercel --prod
```

## 🔧 주요 변경 사항

### 데이터베이스
- ❌ DynamoDB → ✅ PostgreSQL (Railway 제공)
- SQLAlchemy ORM 사용
- Alembic 마이그레이션

### 파일 스토리지
- ❌ AWS S3 → ✅ Railway Volumes
- 로컬 파일 시스템 기반 스토리지
- `/data` 경로에 마운트

### 인프라
- ❌ Lambda + API Gateway → ✅ Railway 컨테이너
- ❌ CloudFront → ✅ Railway CDN
- ❌ SST → ✅ Docker 기반 배포

## 📊 예상 비용

### Railway 프리 티어
- **$5 무료 크레딧/월**
- PostgreSQL: 포함
- 컨테이너: 포함
- Volumes: 포함

### 유료 시 예상 비용
- **Hobby Plan**: $5/월
- **추가 사용량**: 종량제
- **총 예상**: $10-15/월

### Vercel 프론트엔드
- **무료**: Hobby 플랜
- 월 100GB 대역폭
- 무제한 배포

## 🔐 보안 설정

### 1. 비밀번호 변경
```bash
# Railway 환경변수에서 설정
SIMPLE_AUTH_PASSWORD=매우_강력한_비밀번호
```

### 2. CORS 제한
```bash
# 프론트엔드 도메인만 허용
CORS_ORIGINS=https://your-app.vercel.app,https://your-app.railway.app
```

### 3. HTTPS 강제
Railway는 자동으로 HTTPS 제공 ✅

## 📈 모니터링

### Railway 대시보드
- **Metrics**: CPU, 메모리, 네트워크 사용량
- **Logs**: 실시간 로그 스트리밍
- **Deployments**: 배포 히스토리

### 헬스 체크
```bash
curl https://your-backend.railway.app/health
```

## 🛠️ 문제 해결

### 데이터베이스 연결 오류
```bash
# Railway 대시보드에서 DATABASE_URL 확인
railway variables

# 로컬 테스트
export DATABASE_URL="..."
python -c "from app.models.database import engine; engine.connect()"
```

### 마이그레이션 실패
```bash
# 수동 마이그레이션
railway run alembic upgrade head

# 롤백
railway run alembic downgrade -1
```

### Volume 권한 오류
```bash
# Dockerfile에서 사용자 권한 확인
# Railway Volume은 자동으로 마운트됨
```

## 🔄 업데이트 배포

```bash
# 코드 변경 후
git add .
git commit -m "Update: 변경사항"
git push

# Railway 자동 배포 (GitHub 연동 시)
# 또는 수동 배포
railway up
```

## 📝 환경별 설정

### 로컬 개발
```bash
export ENVIRONMENT=local
export DATABASE_URL=sqlite:///./voj_dev.db
python -m app.main
```

### Railway 프로덕션
```bash
export ENVIRONMENT=railway
export DATABASE_URL=${{Postgres.DATABASE_URL}}
export RAILWAY_VOLUME_MOUNT_PATH=/data
```

## 🎯 다음 단계

1. ✅ 기본 배포 완료
2. 🔄 도메인 연결 (선택)
3. 📊 모니터링 설정
4. 🔐 백업 전략 수립
5. 📈 스케일링 계획

## 💡 팁

- **데이터베이스 백업**: Railway 대시보드에서 자동 백업 활성화
- **로그 모니터링**: `railway logs -f` 실시간 로그 확인
- **환경변수 관리**: `.env.railway.example` 참고
- **비용 최적화**: 사용하지 않는 서비스 비활성화

## 🆘 지원

- [Railway 문서](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [GitHub Issues](https://github.com/your-repo/issues)
