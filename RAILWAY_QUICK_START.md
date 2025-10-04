# Railway 빠른 시작 가이드

현재 상태: Railway 프로젝트 생성 완료 ✅

## 🚨 중요: Railway 대시보드 설정 필요

Railway CLI에서 TTY 제한으로 인해 대시보드에서 직접 설정해야 합니다.

### 1️⃣ Railway 대시보드 접속

프로젝트 URL: https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29

### 2️⃣ PostgreSQL 데이터베이스 추가

1. **New** 버튼 클릭
2. **Database** 선택
3. **PostgreSQL** 선택
4. 자동으로 `DATABASE_URL` 환경변수 생성됨 ✅

### 3️⃣ Volume 추가 (파일 스토리지)

1. **New** 버튼 클릭
2. **Volume** 선택
3. 설정:
   - **Name**: `voj-storage`
   - **Mount Path**: `/data`
4. 서비스에 Volume 연결

### 4️⃣ 백엔드 서비스 설정

#### A. 서비스가 이미 생성된 경우
1. 서비스 클릭
2. **Settings** → **Source** 확인
3. Root Directory: `backend` 설정

#### B. 새 서비스 생성
1. **New** → **GitHub Repo** 선택
2. 저장소 선택
3. **Settings** → **Source**:
   - Root Directory: `backend`
   - Watch Paths: `backend/**`

### 5️⃣ 환경변수 설정

**Variables** 탭에서 다음 환경변수 추가:

```bash
# 필수
ENVIRONMENT=railway
PORT=8000

# 인증 (보안 강화!)
SIMPLE_AUTH_USERNAME=admin
SIMPLE_AUTH_PASSWORD=여기에_강력한_비밀번호_입력

# CORS (나중에 프론트엔드 URL 추가)
CORS_ORIGINS=*
ALLOWED_HOSTS=*

# 로깅
LOG_LEVEL=INFO

# 프로젝트 정보
PROJECT_NAME=VOJ Audiobooks API
API_V1_STR=/api/v1
```

### 6️⃣ Volume 마운트 확인

**Settings** → **Volumes** 탭에서:
- Volume `voj-storage`가 `/data`에 마운트되었는지 확인
- 없으면 **Add Volume** 클릭하여 연결

### 7️⃣ 배포 트리거

**Deployments** 탭에서:
1. **Deploy** 버튼 클릭
2. 또는 GitHub에 push하면 자동 배포

---

## 🖥️ CLI에서 배포 (대시보드 설정 완료 후)

### 서비스 ID 확인
```bash
# Railway 대시보드에서 서비스 ID 복사
# URL: https://railway.com/project/.../service/[서비스ID]
```

### 배포 실행
```bash
cd backend

# 서비스 ID 지정하여 배포
railway up --service [서비스ID]

# 또는 대시보드에서 서비스 선택 후
railway link
railway up
```

---

## ✅ 배포 확인

### 1. 로그 확인
```bash
railway logs --service [서비스ID]
```

### 2. 헬스 체크
```bash
# 대시보드에서 생성된 도메인 확인
curl https://your-service.railway.app/health
```

### 3. API 테스트
```bash
curl https://your-service.railway.app/api/v1/health
```

---

## 🔧 문제 해결

### "Deploy failed" 오류
1. **Logs** 탭에서 빌드 로그 확인
2. Dockerfile 경로 확인: `backend/Dockerfile`
3. Root Directory 설정: `backend`

### DATABASE_URL 없음
1. PostgreSQL 서비스 생성 확인
2. Variables 탭에서 `DATABASE_URL` 자동 생성 확인
3. 수동 추가: `postgresql://user:pass@host:port/db`

### Volume 마운트 안됨
1. Settings → Volumes → Add Volume
2. Mount Path: `/data`
3. 재배포 필요

### 환경변수 적용 안됨
1. Variables 탭에서 환경변수 확인
2. 변경 후 **Redeploy** 필요

---

## 📱 다음 단계

### 1. 데이터베이스 마이그레이션
```bash
# Railway CLI로 실행
railway run alembic upgrade head

# 또는 대시보드에서 one-off command
# Command: alembic upgrade head
```

### 2. 프론트엔드 배포 (Vercel)
```bash
cd ../frontend

# Vercel 배포
vercel

# 환경변수 설정
vercel env add NEXT_PUBLIC_API_URL
# 입력: https://your-backend.railway.app

vercel env add NEXT_PUBLIC_API_BASE
# 입력: https://your-backend.railway.app/api/v1

# 프로덕션 배포
vercel --prod
```

### 3. CORS 업데이트
Railway Variables에서 CORS_ORIGINS 업데이트:
```bash
CORS_ORIGINS=https://your-frontend.vercel.app,https://your-frontend.railway.app
```

---

## 💰 비용 모니터링

**Dashboard** → **Usage**에서:
- CPU/메모리 사용량 확인
- 네트워크 사용량 확인
- 예상 비용 확인

**Hobby Plan**: $5/월부터 시작

---

## 🆘 추가 도움

- [Railway 문서](https://docs.railway.app/)
- [Discord](https://discord.gg/railway)
- [GitHub Issues](https://github.com/railwayapp/railway/issues)
