# Railway 배포 최종 수정

## ✅ 완료된 작업
- Dockerfile 수정: 프로젝트 루트에서 실행 가능하도록 변경
- railway.toml 업데이트: `dockerfilePath = "backend/Dockerfile"`
- Git push 완료: Railway 자동 배포 트리거

## 🔧 Railway 대시보드에서 확인할 사항

### 1. Settings → Source 설정

**중요: Root Directory를 비워야 합니다!**

```
Root Directory: (비워두기 - 삭제)
```

현재 설정이 `backend`로 되어 있다면:
1. Settings → Source
2. Root Directory 필드의 `backend` 삭제
3. 완전히 비워두기
4. Save

### 2. Settings → Deploy 확인

```
Build Method: Dockerfile
Dockerfile Path: backend/Dockerfile
```

### 3. 배포 상태 확인

1. **Deployments** 탭
2. 최신 배포 확인 (자동으로 시작됨)
3. **View Logs** 클릭
4. 빌드 로그 확인:
   - `Successfully built` 확인
   - `Running upgrade ... -> 001_initial` (마이그레이션)
   - 에러 없이 완료

### 4. 배포 완료 후 테스트

```bash
# 헬스 체크 (30초~1분 후)
curl https://voj-backend-production.up.railway.app/health

# 예상 응답:
# {"status":"healthy","environment":"railway"}
```

---

## 🐛 여전히 404 에러가 나는 경우

### Root Directory가 비워지지 않은 경우:

**Railway 대시보드에서:**
1. Settings → Source
2. Root Directory: **완전히 삭제** (공백도 없이)
3. Save
4. Deployments → Redeploy

### 빌드 실패하는 경우:

**로그에서 확인:**
```
COPY backend/pyproject.toml ... -> No such file or directory
```

**해결:**
- GitHub 저장소에 변경사항이 반영되었는지 확인
- Railway가 올바른 브랜치를 보고 있는지 확인 (main)

---

## 📋 단계별 체크리스트

- [x] Dockerfile 수정 완료
- [x] Git push 완료
- [ ] Railway Settings → Source → Root Directory 비우기 ⚠️
- [ ] Railway 자동 배포 확인
- [ ] 빌드 로그에서 에러 확인
- [ ] 헬스 체크 성공

---

## 🎯 현재 해야 할 일

1. **Railway 대시보드 접속**
   ```
   https://railway.com/project/ca0cd363-66b4-41f5-bbcb-b2c49ce7ba29
   ```

2. **백엔드 서비스 → Settings → Source**

3. **Root Directory 삭제** (가장 중요!)
   - 현재: `backend`
   - 변경: ` ` (완전히 비우기)

4. **Save 클릭**

5. **Deployments 탭에서 새 배포 확인**
   - 약 2-3분 소요

6. **배포 완료 후 테스트**
   ```bash
   curl https://voj-backend-production.up.railway.app/health
   ```

---

## 💡 설명

### 왜 Root Directory를 비워야 하나?

**이전 설정:**
```
Root Directory: backend
Dockerfile Path: Dockerfile
→ Railway가 backend/Dockerfile을 찾음
→ 하지만 Dockerfile 내부에서 backend/app을 찾으려 함 (오류!)
```

**새 설정:**
```
Root Directory: (비어있음)
Dockerfile Path: backend/Dockerfile
→ Railway가 프로젝트 루트에서 backend/Dockerfile을 찾음
→ Dockerfile이 backend/app을 정상적으로 복사 ✅
```

---

## ✨ 다음 단계 (배포 성공 후)

### 1. 프론트엔드 배포

```bash
cd frontend
vercel

# 환경변수 설정
vercel env add NEXT_PUBLIC_API_URL
# https://voj-backend-production.up.railway.app

vercel env add NEXT_PUBLIC_API_BASE
# https://voj-backend-production.up.railway.app/api/v1

# 프로덕션 배포
vercel --prod
```

### 2. CORS 업데이트

Railway Variables:
```
CORS_ORIGINS=https://your-frontend.vercel.app
```

---

**지금 바로 Railway 대시보드에서 Root Directory를 삭제하고, 새 배포를 확인해주세요!**
