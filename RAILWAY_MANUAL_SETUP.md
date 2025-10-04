# Railway 수동 설정 가이드

Railway CLI의 제약으로 인해 웹 대시보드에서 직접 설정하는 것을 권장합니다.

## 🌐 Railway 대시보드 접속

**프로젝트 URL**: https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29

---

## 1️⃣ PostgreSQL 데이터베이스 추가

### 단계:
1. 프로젝트 대시보드 접속
2. 오른쪽 상단 **"+ New"** 버튼 클릭
3. **"Database"** 선택
4. **"Add PostgreSQL"** 클릭

### 결과:
- ✅ PostgreSQL 서비스 자동 생성
- ✅ `DATABASE_URL` 환경변수 자동 생성
- ✅ 모든 서비스에서 접근 가능

---

## 2️⃣ Volume 추가 (파일 스토리지)

### 단계:
1. **"+ New"** → **"Volume"** 클릭
2. 설정:
   - **Name**: `voj-storage`
   - **Mount Path**: `/data`
3. **"Add"** 클릭
4. 생성된 Volume을 백엔드 서비스에 연결:
   - 서비스 클릭 → **Settings** → **Volumes**
   - **"Mount Volume"** 클릭
   - Volume 선택 → Mount Path: `/data`

### 결과:
- ✅ 영구 스토리지 생성
- ✅ `/data` 경로에 마운트
- ✅ 재배포 시에도 데이터 유지

---

## 3️⃣ 백엔드 서비스 확인/생성

### 서비스가 이미 있는 경우:
1. 서비스 클릭
2. **Settings** → **General**
   - Service Name: `backend` (원하는 이름)
3. **Settings** → **Source**
   - Root Directory: **`backend`** ⚠️ 중요!
   - Watch Paths: `backend/**`

### 새 서비스 생성:
1. **"+ New"** → **"GitHub Repo"** 클릭
2. 저장소 선택 및 권한 부여
3. **Settings** 설정:
   - Root Directory: `backend`
   - Build Command: (비워두기 - Dockerfile 사용)
   - Start Command: (비워두기 - Dockerfile CMD 사용)

---

## 4️⃣ 환경변수 설정

### 단계:
1. 백엔드 서비스 클릭
2. **Variables** 탭 클릭
3. **"+ New Variable"** 클릭하여 추가:

### 필수 환경변수:

```bash
# 환경 설정
ENVIRONMENT=railway
PORT=8000

# 인증 (⚠️ 강력한 비밀번호 사용!)
SIMPLE_AUTH_USERNAME=admin
SIMPLE_AUTH_PASSWORD=YOUR_STRONG_PASSWORD_HERE

# CORS (나중에 프론트엔드 URL 추가)
CORS_ORIGINS=*
ALLOWED_HOSTS=*

# 로깅
LOG_LEVEL=INFO

# 프로젝트 정보
PROJECT_NAME=VOJ Audiobooks API
API_V1_STR=/api/v1
```

### 자동 생성된 변수 (확인만):
- `DATABASE_URL` - PostgreSQL 연결 URL (자동)
- `RAILWAY_VOLUME_MOUNT_PATH` - Volume 마운트 경로 (자동)

---

## 5️⃣ 배포 설정 확인

### Settings → Deploy:
- **Build Method**: Dockerfile
- **Dockerfile Path**: `Dockerfile` (Root Directory가 backend이므로)
- **Watch Paths**: `backend/**`
- **Auto-deploy**: ✅ 활성화 (GitHub push 시 자동 배포)

---

## 6️⃣ 배포 트리거

### 방법 1: 대시보드에서 배포
1. **Deployments** 탭
2. **"Deploy"** 버튼 클릭
3. 빌드 로그 확인

### 방법 2: GitHub Push로 자동 배포
```bash
git add .
git commit -m "Configure Railway deployment"
git push
```

### 방법 3: CLI로 배포 (설정 완료 후)
```bash
cd backend
railway up
```

---

## 7️⃣ 데이터베이스 마이그레이션

배포 성공 후, 데이터베이스 스키마를 생성해야 합니다.

### Railway CLI 사용:
```bash
cd backend
railway run alembic upgrade head
```

### 대시보드 사용:
1. 서비스 클릭 → **Settings** → **Deploy**
2. **One-off Command** 실행:
   ```bash
   alembic upgrade head
   ```

---

## 8️⃣ 배포 확인

### 1. 로그 확인
- 대시보드: **Deployments** → 최신 배포 클릭 → **View Logs**
- CLI: `railway logs -f`

### 2. 도메인 확인
- **Settings** → **Networking** → **Public Networking**
- **Generate Domain** 클릭하여 도메인 생성
- 예: `backend-production-xxxx.up.railway.app`

### 3. 헬스 체크
```bash
curl https://your-backend.railway.app/health

# 응답 예시:
# {"status":"healthy","environment":"railway"}
```

### 4. API 테스트
```bash
curl https://your-backend.railway.app/api/v1/health
```

---

## 🔧 문제 해결

### ❌ "Build Failed" 오류

**확인 사항:**
1. Root Directory가 `backend`로 설정되었는지 확인
2. Dockerfile이 `backend/Dockerfile`에 있는지 확인
3. pyproject.toml, poetry.lock이 `backend/` 안에 있는지 확인

**해결:**
- Settings → Source → Root Directory: `backend`

---

### ❌ "DATABASE_URL not found" 오류

**확인:**
1. PostgreSQL 서비스가 생성되었는지 확인
2. Variables 탭에 `DATABASE_URL`이 있는지 확인

**해결:**
- PostgreSQL 서비스 재생성
- 또는 수동으로 DATABASE_URL 추가

---

### ❌ Volume 마운트 안됨

**확인:**
1. Volume이 생성되었는지 확인
2. 서비스에 Volume이 연결되었는지 확인

**해결:**
1. Settings → Volumes → Mount Volume
2. 재배포 (변경사항 적용 위해)

---

### ❌ Port Binding 오류

**확인:**
- `PORT` 환경변수가 설정되었는지 확인

**해결:**
```bash
PORT=8000
```

---

## 📊 배포 완료 체크리스트

- [ ] PostgreSQL 서비스 생성
- [ ] Volume 생성 및 마운트 (`/data`)
- [ ] 환경변수 설정 (최소 6개)
- [ ] Root Directory 설정 (`backend`)
- [ ] 배포 성공 (Build Logs 확인)
- [ ] 데이터베이스 마이그레이션 실행
- [ ] 도메인 생성
- [ ] 헬스 체크 성공 (`/health`)

---

## 🎯 다음 단계

### 1. 프론트엔드 배포 (Vercel)
```bash
cd frontend
vercel

# 환경변수 설정
vercel env add NEXT_PUBLIC_API_URL
# 입력: https://your-backend.railway.app

vercel env add NEXT_PUBLIC_API_BASE
# 입력: https://your-backend.railway.app/api/v1

# 프로덕션 배포
vercel --prod
```

### 2. CORS 업데이트
프론트엔드 URL을 알게 되면, Railway Variables에서 업데이트:
```bash
CORS_ORIGINS=https://your-frontend.vercel.app
```

### 3. 커스텀 도메인 (옵션)
- Settings → Networking → Custom Domain
- 도메인 연결 및 DNS 설정

---

## 💰 비용 확인

**Dashboard** → **Usage**:
- CPU/메모리 사용량
- 네트워크 트래픽
- 예상 월별 비용

**Hobby Plan**: $5/월 + 사용량

---

## 📞 도움 받기

- **Railway 문서**: https://docs.railway.app/
- **Discord**: https://discord.gg/railway
- **Status**: https://status.railway.app/
