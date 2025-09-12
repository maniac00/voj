# VOJ Audiobooks

VOJ Audiobooks - 오디오북 스트리밍 플랫폼

## 개발 환경 설정

### 로컬 개발 환경

```bash
# 로컬 개발 환경 자동 설정
./scripts/setup-local.sh
```

### 백엔드 실행

```bash
cd backend
poetry run python3 -m app.main
```

### 프론트엔드 실행

```bash
npm run dev
```

## 기술 스택

- **Backend**: FastAPI, Python 3.12+
- **Frontend**: Next.js 15, React 19, TypeScript
- **Database**: DynamoDB
- **Storage**: S3 (프로덕션), Local File System (개발)
- **CDN**: CloudFront
- **Auth**: AWS Cognito

