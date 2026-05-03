# Railway 404 에러 문제 해결

## 🔴 증상
```
{"status":"error","code":404,"message":"Application not found"}
```

## 🔍 원인 체크리스트

### 1. 배포 상태 확인

**Railway 대시보드:**
1. https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29
2. 백엔드 서비스 클릭
3. **Deployments** 탭 확인

**확인 사항:**
- [ ] 최신 배포가 "Success" 상태인가?
- [ ] 빌드 로그에 에러가 없는가?
- [ ] 런타임 로그가 정상인가?

### 2. 서비스 설정 확인

**Settings → Source:**
- [ ] Root Directory: `backend` ✅
- [ ] Watch Paths: `backend/**` 또는 비워두기

**Settings → Deploy:**
- [ ] Build Method: Dockerfile
- [ ] Dockerfile Path: `Dockerfile`

### 3. 환경변수 확인

**Variables 탭:**
```bash
# 필수 환경변수
ENVIRONMENT=railway          ✅
PORT=8000                    ✅
DATABASE_URL=(자동 생성)     ✅

# 확인 필요
RAILWAY_VOLUME_MOUNT_PATH=/data
```

### 4. PORT 바인딩 확인

**문제:** Railway는 동적 PORT를 할당하는데 앱이 8000으로 고정되어 있을 수 있음

**해결:**
- Variables 탭에서 `PORT` 제거 (Railway가 자동 설정)
- 또는 Dockerfile CMD 확인

---

## 🛠️ 해결 방법

### 방법 1: 로그 확인 (대시보드)

1. 백엔드 서비스 → **Deployments**
2. 최신 배포 클릭
3. **View Logs** 클릭
4. 에러 메시지 확인

**찾아야 할 것:**
- `ModuleNotFoundError`
- `ImportError`
- `PORT binding failed`
- `psycopg2` 오류

### 방법 2: Root Directory 재확인

**Settings → Source:**
```
Root Directory: backend
```

**주의:**
- `backend`로 설정 시 Dockerfile은 `backend/Dockerfile` 위치
- Dockerfile 내부의 `COPY app ./app`는 `backend/app`를 복사

### 방법 3: Dockerfile 확인

현재 Dockerfile이 올바른지 확인:

```dockerfile
# Builder stage
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# Runtime stage
COPY --from=builder /app/app /app/app
COPY --from=builder /app/alembic /app/alembic

# ENV
ENV PYTHONPATH="/app"

# CMD
CMD ["sh", "-c", "/opt/venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60"]
```

### 방법 4: 강제 재배포

**Deployments 탭:**
1. 최신 배포 우측 메뉴 (...)
2. **Redeploy** 클릭
3. 로그 확인

---

## 🧪 디버깅 단계

### 1. 로컬 Docker 테스트

```bash
cd backend

# 로컬에서 Docker 빌드
docker build -t voj-backend .

# 실행
docker run -p 8000:8000 \
  -e DATABASE_URL='postgresql://...' \
  -e ENVIRONMENT=railway \
  voj-backend

# 테스트
curl http://localhost:8000/health
```

### 2. Railway 환경변수 추가

Variables 탭에서 추가:

```bash
# 디버그 모드
LOG_LEVEL=DEBUG

# Python 출력 버퍼링 해제 (로그 즉시 출력)
PYTHONUNBUFFERED=1
```

재배포 후 로그 확인

### 3. 헬스체크 엔드포인트 변경

Dockerfile에 healthcheck 추가 확인:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8000}/health || exit 1
```

---

## 📋 체크리스트 순서

1. **배포 로그 확인**
   - Deployments → View Logs
   - 빌드/런타임 에러 찾기

2. **Root Directory 확인**
   - Settings → Source → `backend`

3. **PORT 환경변수 제거**
   - Variables → PORT 삭제
   - Railway 자동 할당 사용

4. **강제 재배포**
   - Deployments → Redeploy

5. **Dockerfile 경로 확인**
   - `backend/Dockerfile` 존재 확인
   - 내용 검증

---

## 🔧 일반적인 원인과 해결

### 원인 1: Root Directory 설정 오류
```
Root Directory: backend (올바름)
Root Directory: .        (틀림)
```

### 원인 2: PORT 바인딩 실패
```bash
# Variables에서 PORT 제거
# Railway가 자동으로 $PORT 주입
```

### 원인 3: Python 경로 문제
```dockerfile
ENV PYTHONPATH="/app"  # 올바름
ENV PYTHONPATH="/app/backend"  # 틀림
```

### 원인 4: 의존성 누락
```bash
# poetry.lock 최신 상태 확인
poetry lock
git add poetry.lock
git commit -m "Update poetry.lock"
git push
```

---

## 🎯 다음 액션

1. **Railway 대시보드 → Deployments → View Logs**
   - 에러 메시지 확인

2. **로그에서 찾은 에러 알려주세요**
   - 구체적인 해결 방법 제시

3. **Settings 스크린샷 공유** (선택)
   - Source, Deploy 설정 확인
