# VOJ Audiobooks

VOJ Audiobooks - 시각장애인을 위한 오디오북 스트리밍 플랫폼

## 🚀 배포 환경

### Railway 프로덕션 (현재)
- **비용**: ~$10-15/월
- **데이터베이스**: PostgreSQL
- **스토리지**: Railway Volumes
- **배포**: [Railway 가이드](./RAILWAY_DEPLOYMENT.md) 참고

### AWS (레거시 - 선택사항)
- AWS 배포를 원하는 경우 `poetry install -E aws` 실행
- 자세한 내용은 [마이그레이션 요약](./MIGRATION_SUMMARY.md) 참고

## 💻 개발 환경 설정

### 1. 로컬 개발 환경

```bash
# 로컬 개발 환경 자동 설정 (선택사항)
./scripts/setup-local.sh
```

### 2. 백엔드 실행

```bash
cd backend

# 의존성 설치
poetry install

# 로컬 데이터베이스 마이그레이션
export DATABASE_URL="sqlite:///./voj_dev.db"
alembic upgrade head

# 개발 서버 실행
poetry run python3 -m app.main
```

### 3. 프론트엔드 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI, Python 3.12+
- **Database**: PostgreSQL (프로덕션), SQLite (개발)
- **ORM**: SQLAlchemy
- **Migration**: Alembic

### Frontend
- **Framework**: Next.js 14, React 18, TypeScript
- **UI**: Radix UI, Tailwind CSS
- **State**: Zustand, React Hook Form

### Infrastructure
- **Hosting**: Railway (Backend), Vercel (Frontend)
- **Database**: Railway PostgreSQL
- **Storage**: Railway Volumes
- **CDN**: Railway CDN

## 📚 문서

- [Railway 배포 가이드](./RAILWAY_DEPLOYMENT.md)
- [마이그레이션 요약](./MIGRATION_SUMMARY.md)

