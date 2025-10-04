# Railway 새 서비스 생성 가이드

## 🔴 문제
Railway 서비스의 빌드 캐시가 완전히 고착되어 새 Dockerfile을 인식하지 못함

## ✅ 해결: 새 서비스 생성

### 1단계: 기존 서비스 삭제 (선택사항)

Railway 대시보드:
1. 백엔드 서비스 클릭
2. Settings → General
3. 하단 "Delete Service" (나중에 해도 됨)

### 2단계: 새 서비스 생성

1. **프로젝트 대시보드** 메인 화면
2. **"+ New"** 버튼 클릭
3. **"GitHub Repo"** 선택
4. 저장소 선택: `maniac00/voj`
5. **"Deploy Now"** 클릭

### 3단계: 서비스 설정

**Settings → Source:**
```
Root Directory: (비워두기)
```

**Settings → Deploy:**
```
Build Method: Dockerfile
Dockerfile Path: backend/Dockerfile
```

### 4단계: 환경변수 설정

**Variables 탭:**
```bash
ENVIRONMENT=railway
SIMPLE_AUTH_USERNAME=admin
SIMPLE_AUTH_PASSWORD=강력한비밀번호
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

### 5단계: PostgreSQL 연결

**Variables 탭:**
- PostgreSQL 서비스가 같은 프로젝트에 있으면 자동으로 `DATABASE_URL` 생성됨
- 없으면 수동으로 추가:
  ```
  DATABASE_URL=postgresql://postgres:CXPaGWXZnGKHmzJxSKFkLWZorKnaloUo@nozomi.proxy.rlwy.net:19391/railway
  ```

### 6단계: Volume 연결

**Settings → Volumes:**
1. **Mount Volume** 클릭
2. 기존 `voj-storage` 선택
3. Mount Path: `/data`

### 7단계: 도메인 생성

**Settings → Networking:**
1. **Generate Domain** 클릭
2. 도메인 복사

### 8단계: 배포 확인

**Deployments 탭:**
- 빌드 로그 확인
- 성공 시 헬스 체크:
  ```bash
  curl https://새도메인.railway.app/health
  ```

---

## 🎯 예상 결과

새 서비스는 캐시 문제 없이 깨끗하게 빌드됩니다:
```
✓ COPY backend/pyproject.toml
✓ poetry install
✓ COPY backend/app
✓ Successfully built
```

---

## 💡 또는: 다른 Git 브랜치 사용

새 서비스를 만들기 싫다면:

1. 로컬에서 새 브랜치 생성:
   ```bash
   git checkout -b railway-deploy
   git push -u origin railway-deploy
   ```

2. Railway Settings → Source:
   - Branch: `railway-deploy` 선택

3. 재배포
