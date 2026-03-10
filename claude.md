# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

VOJ(Voice of Juan)는 시각장애인을 위한 오디오북 스트리밍 플랫폼. 모노레포로 백엔드, 프론트엔드, 모바일 앱, Cloudflare Workers를 포함한다.

## 개발 명령어

### 백엔드 (FastAPI + SQLAlchemy)
```bash
cd backend
poetry install                                         # 의존성 설치
poetry run uvicorn app.main:app --reload --port 8080   # 개발 서버
poetry run pytest                                      # 테스트
poetry run pytest tests/test_foo.py::test_bar          # 단일 테스트
poetry run alembic upgrade head                        # DB 마이그레이션
poetry run alembic revision --autogenerate -m "msg"    # 마이그레이션 생성
poetry run black . && poetry run isort .               # 포맷팅
poetry run mypy .                                      # 타입 체크
```

### 프론트엔드 (Next.js 14)
```bash
cd frontend
npm install                    # 의존성 설치
npm run dev                    # 개발 서버 (port 3000)
npm run build                  # 프로덕션 빌드
npm run lint                   # ESLint
npm run type-check             # TypeScript 체크
npm test                       # Jest 테스트
```

### 모바일 (Flutter + Riverpod)
```bash
cd mobile
flutter pub get                # 의존성 설치
flutter run                    # 에뮬레이터/디바이스 실행
flutter test                   # 테스트
flutter analyze                # 코드 분석
flutter build apk --release \
  --dart-define=VOJ_API_BASE_URL=https://voj-production.up.railway.app/api/v1  # APK 빌드
```

### Cloudflare Workers
```bash
cd r2-worker     # 또는 cd download-page
npm run dev      # 로컬 개발
npm run deploy   # 배포
```

### 로컬 환경 전체 시작
```bash
./scripts/start-local.sh       # 백엔드(8080) + 프론트엔드(3000) 동시 시작
```

## 아키텍처

### 컴포넌트 구조
- `backend/` — FastAPI REST API. 엔트리: `app/main.py`. API 경로: `/api/v1`. Settings는 `app/settings/factory.py`에서 `ENVIRONMENT` 환경변수 기반 팩토리 패턴.
- `frontend/` — Next.js 14 App Router 관리자 대시보드. `src/app/(admin)/` 하위에 라우트. Tailwind + Radix UI. path alias `@/*`.
- `mobile/` — Flutter 앱. Riverpod 상태관리, just_audio 오디오 재생. `lib/` 내 `core/`, `data/`, `domain/`, `presentation/` 레이어 구분.
- `r2-worker/` — R2 파일 서빙 Worker. HMAC 토큰 검증, APK는 퍼블릭 접근, Range 요청 지원.
- `download-page/` — 정적 다운로드 페이지. `public/metadata.json`에 APK 버전 정보.

### 데이터베이스
- 로컬: SQLite (`voj_dev.db`), 프로덕션: PostgreSQL (Railway)
- 마이그레이션: `alembic/versions/` (001~006)
- SQLite는 ALTER constraint 미지원 → 로컬에서 스키마 변경 시 주의

### 인증
- Firebase Auth + 단순 정적 계정 (MVP)
- 로컬 개발: `LOCAL_BYPASS_ENABLED=true`로 인증 우회 가능
- 모바일: Firebase + 커스텀 리프레시 토큰 (`MobileRefreshTokenSQL`)

### CI/CD
- 백엔드: main 푸시 → GitHub Actions → Railway 자동 배포
- 프론트엔드: main 푸시 → GitHub Actions → Vercel 배포
- 모바일: `scripts/deploy-app.sh` 수동 실행 (빌드 → R2 업로드 → 메타데이터 갱신)

---

# Cloudflare Infrastructure Rules

> ⚠️ 이 문서는 Claude Code가 Cloudflare 설정 시 반드시 따라야 할 최신 규칙입니다.
> 학습 데이터에 있는 오래된 패턴을 사용하지 마세요.

## 설정 파일 포맷

- **반드시 `wrangler.jsonc`를 사용할 것** (`wrangler.toml` 사용 금지)
- Cloudflare 공식 권장 포맷은 wrangler v3.91.0+ 기준 `wrangler.jsonc`임
- `$schema`를 반드시 포함: `"$schema": "node_modules/wrangler/config-schema.json"`
- `compatibility_date`는 `"2025-01-01"` 이상으로 설정
- `compatibility_flags`에 `"nodejs_compat"` 포함

### wrangler.jsonc 기본 템플릿

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2025-01-01",
  "compatibility_flags": ["nodejs_compat"],
  "r2_buckets": [
    {
      "binding": "MY_BUCKET",
      "bucket_name": "my-bucket-name"
    }
  ]
}
```

## R2 설정 규칙

### 자동 프로비저닝 (wrangler v4.45.0+)
- R2 버킷을 수동으로 먼저 생성할 필요 없음
- `wrangler.jsonc`에 바인딩만 추가하면 `wrangler deploy` 시 자동 생성됨
- `bucket_name` 없이 binding만 넣으면 worker 이름을 prefix로 자동 생성
- ❌ 더 이상 `wrangler r2 bucket create <name>`을 별도로 실행하지 않아도 됨
- 자동 프로비저닝 비활성화: `--no-x-provision` 플래그

### R2 바인딩 설정
```jsonc
{
  "r2_buckets": [
    {
      "binding": "MY_BUCKET",        // Worker 코드에서 사용할 변수명
      "bucket_name": "my-bucket",     // 실제 R2 버킷 이름
      "preview_bucket_name": "my-bucket-preview"  // (선택) wrangler dev --remote 시 사용
    }
  ]
}
```

### R2 Worker 코드 패턴 (Module Worker 문법만 사용)
```typescript
// ✅ 올바른 패턴: Module Worker (ES Modules)
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const object = await env.MY_BUCKET.get("my-key");
    // ...
  }
} satisfies ExportedHandler<Env>;

interface Env {
  MY_BUCKET: R2Bucket;
}
```

```javascript
// ❌ 금지: Service Worker (addEventListener) 문법 사용하지 말 것
addEventListener('fetch', event => { ... })
```

### R2 로컬 개발
- `wrangler dev`는 기본적으로 로컬 스토리지에 R2 데이터를 저장함
- 원격 R2 버킷 사용하려면: 바인딩에 `"remote": true` 설정

## Cloudflare Pages 관련

- ❌ Cloudflare Pages는 2025년 4월 deprecated됨
- ✅ 정적 사이트도 Workers를 사용할 것
- `pages_build_output_dir` 속성으로 정적 파일 디렉토리 지정

## 배포 명령어

```bash
# 개발
npx wrangler dev

# 배포
npx wrangler deploy

# ❌ 사용 금지 (deprecated)
# wrangler pages publish
# wrangler publish
```

## 프로젝트 생성

```bash
# 새 프로젝트 생성 시 create-cloudflare CLI 사용
npm create cloudflare@latest

# ❌ wrangler init은 레거시
```

## 프로덕션 서비스 주소

| 서비스 | URL |
|--------|-----|
| 백엔드 (Railway) | `https://voj-production.up.railway.app` |
| 프론트엔드 (Vercel) | `https://voj-admin.vercel.app` |
| 다운로드 페이지 (Workers) | `https://voj-download.7wario.workers.dev` |
| R2 파일 서빙 (Workers) | `https://voj-releases.7wario.workers.dev` |

- 모바일 APK 빌드 시 반드시 위 백엔드 주소를 사용할 것:
  `--dart-define=VOJ_API_BASE_URL=https://voj-production.up.railway.app/api/v1`
- ❌ `voj-api.up.railway.app`는 **존재하지 않는 잘못된 주소** — 절대 사용 금지

## 배포

### 배포 스크립트

| 스크립트 | 용도 |
|----------|------|
| `scripts/deploy-app.sh` | 모바일 앱 빌드 → R2 업로드 → metadata 업데이트 → 다운로드 페이지 배포 |
| `scripts/deploy-frontend.sh` | Vercel 프론트엔드 프로덕션 배포 |
| `scripts/deploy-backend.sh` | Railway 백엔드 배포 안내 및 헬스체크 |

- 백엔드는 main 브랜치 푸시 시 Railway가 자동 배포
- 앱 배포(`deploy-app.sh`)는 download-page 재배포를 자동 포함

### 모바일 앱 버전 관리

- APK를 새로 빌드할 때마다 **반드시 버전을 올릴 것**
- 버전은 `mobile/pubspec.yaml`의 `version` 필드에서 관리 (형식: `X.Y.Z+buildNumber`)
- patch 수정은 Z를, 기능 추가는 Y를, 큰 변경은 X를 올림
- `+` 뒤의 buildNumber도 매 빌드마다 1씩 증가
- R2에는 버전별 파일(`voice-of-juan-v{VERSION}.apk`)만 업로드 (latest.apk 사용하지 않음)
- 로그인 화면 하단 버전 표시는 `package_info_plus`로 `pubspec.yaml`에서 자동 읽기 (수동 업데이트 불필요)

## 중요 참고사항

- 확실하지 않은 Cloudflare 설정이 있으면, 반드시 공식 문서를 웹 검색해서 확인할 것
- 공식 문서: https://developers.cloudflare.com/r2/
- Wrangler 설정 문서: https://developers.cloudflare.com/workers/wrangler/configuration/
