# Railway runc 에러 해결

## 🔴 에러
```
runc run failed: container process is already dead
```

## 원인
1. Railway 빌더 인프라 일시적 문제
2. 메모리 부족
3. 빌드 타임아웃

## 해결 방법

### 1. 단순 재배포 (가장 효과적)
Railway Deployments 탭:
- 최신 배포 우측 **(...)** → **Redeploy**

대부분 이것만으로 해결됩니다.

### 2. Dockerfile 간소화
메모리 사용량을 줄이기 위해 멀티스테이지 빌드 최적화

### 3. Railway Service 재시작
Settings → General → **Restart Service**
