# Vercel 강제 재빌드 방법

## 문제
`next.config.js`의 rewrites는 **빌드 타임**에 환경변수를 읽습니다.
환경변수를 변경해도 기존 빌드가 캐시되어 있으면 반영되지 않습니다.

## 해결 방법

### 옵션 1: Vercel 대시보드에서 재배포 (권장)
1. Vercel Dashboard → 프로젝트 선택
2. Deployments 탭
3. 최신 배포 클릭
4. 우측 상단 ⋯ 메뉴
5. **"Redeploy"** 클릭
6. ✅ **"Use existing Build Cache" 체크 해제!** (중요!)
7. "Redeploy" 버튼 클릭

### 옵션 2: 빈 커밋 푸시
```bash
git commit --allow-empty -m "Force Vercel rebuild to apply env vars"
git push
```

### 옵션 3: vercel.json으로 환경변수 하드코딩 (최종 수단)
프로젝트에 `vercel.json` 생성:
```json
{
  "env": {
    "NEXT_PUBLIC_API_URL": "https://voj-production.up.railway.app"
  }
}
```

## 확인
재배포 후 브라우저 콘솔에서:
```
🔬 Request Inspector
  Response URL: https://voj-production.up.railway.app/api/v1/health
```

`https://`로 시작하는지 확인!
