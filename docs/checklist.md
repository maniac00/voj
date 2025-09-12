# 📋 시각장애인용 오디오북 MVP 개발 체크리스트

## 진행 상황 개요
- [x] **1. 개발 환경 구축** (8/8)
- [ ] **2. 인프라 구성** (0/12) 
- [ ] **3. 백엔드 개발** (0/15)
- [ ] **4. 프론트엔드 개발** (0/10)
- [ ] **5. 통합 테스트** (0/6)
- [ ] **6. 배포 및 운영** (0/8)

---

## 1. 개발 환경 구축 ✅

### 1.1 로컬 개발 환경 설정 ✅
- [x] **1.1.1** Node.js 18+ 설치 확인 (v24.7.0 설치됨)
- [x] **1.1.2** Python 3.9+ 설치 확인 (v3.13.7 설치됨)
- [x] **1.1.3** FFmpeg 설치 (Homebrew) (v8.0 설치됨, ffprobe 포함)
- [x] **1.1.4** Docker 설치 (DynamoDB Local용) (v28.3.3 설치됨, Compose v2.39.2 포함)
- [x] **1.1.5** 프로젝트 클론 및 초기 설정
  - [x] **1.1.5.1** Git 저장소 초기화 및 GitHub 생성 (https://github.com/maniac00/voj)
  - [x] **1.1.5.2** `env.local.example` 파일 생성 (환경 변수 템플릿 + .gitignore 추가)
  - [x] **1.1.5.3** `pyproject.toml` 파일 생성 (Poetry 기반, FastAPI, AWS SDK, DynamoDB, 테스트 도구 포함)
  - [x] **1.1.5.4** `package.json` 파일 생성 (Next.js 15, React 19, Shadcn UI, AWS SDK 포함)

### 1.2 스크립트 및 설정 파일 생성 ✅
- [x] **1.2.1** `scripts/setup-local.sh` 스크립트 작성 (Poetry 기반, 의존성 확인, 환경 설정, DynamoDB Local 자동화)
- [x] **1.2.2** `docker-compose.yml` 파일 작성 (DynamoDB Local + Admin UI, 헬스체크 포함)
- [x] **1.2.3** `scripts/create-local-tables.py` 스크립트 작성 (Books/AudioChapters 테이블, GSI, 샘플 데이터 포함)
- [x] **1.2.4** 로컬 환경 변수 설정 (`.env.local`) (FFmpeg 경로 확인 완료)

---

## 2. 인프라 구성 (AWS)

### 2.1 기본 AWS 설정 ✅
- [x] **2.1.1** AWS 계정 생성 및 CLI 설정 (계정: 529088277581, 사용자: voj-dev, 리전: ap-northeast-2)
- [x] **2.1.2** IAM 사용자 확인 (voj-dev 사용자 존재, S3 권한 확인됨)
  - [x] **2.1.2.1** 추가 권한 설정 완료 (DynamoDB, Cognito, CloudFront, Lambda)
  - [x] **2.1.2.2** 정책 할당량 문제 해결 (통합 정책 생성 완료)
- [x] **2.1.3** AWS 리전 설정 (ap-northeast-2) (설정 파일 확인, 서울 리전 접근 가능)

### 2.2 인증 및 권한 관리 ✅
- [x] **2.2.1** Cognito User Pool 생성 (어드민용)
  - [x] **2.2.1.1** 사용자 풀 기본 설정 (ID: ap-northeast-2_7L8xLv4Ex, 이메일 인증, 관리자 전용)
  - [x] **2.2.1.2** 앱 클라이언트 생성 (Client ID: 5q2cjl9jrma7868bhsg4vvminr, OAuth 코드 플로우)
  - [x] **2.2.1.3** 도메인 설정 (도메인: voj-admin-auth, CloudFront: d2gcbvkpcschxy.cloudfront.net)
- [x] **2.2.2** IAM 역할 및 정책 생성
  - [x] **2.2.2.1** Lambda 실행 역할 (API용) (역할: voj-lambda-api-role, 정책 연결 완료)
  - [x] **2.2.2.2** Lambda 실행 역할 (인코딩용) (역할: voj-lambda-encoding-role, 정책 연결 완료)
  - [x] **2.2.2.3** S3 접근 정책 (Lambda 역할에 포함됨)
  - [x] **2.2.2.4** DynamoDB 접근 정책 (Lambda 역할에 포함됨)

### 2.3 데이터베이스 설정
- [x] **2.3.1** DynamoDB 테이블 생성
  - [x] **2.3.1.1** Books 테이블 (PK: book_id) (테이블명: voj-books-prod, 상태: ACTIVE, 태그 포함)
  - [x] **2.3.1.2** AudioChapters 테이블 (PK: book#{book_id}, SK: order#{0001}) (테이블명: voj-audio-chapters-prod, 상태: ACTIVE)
  - [x] **2.3.1.3** GSI 설정 (audio_id 기반 조회용) (GSI1: audio_id + created_at, 상태: ACTIVE)

### 2.4 스토리지 및 CDN 설정
- [x] **2.4.1** S3 버킷 생성 및 설정
  - [x] **2.4.1.1** 비공개 버킷 생성 (버킷명: voj-audiobooks-prod, 리전: ap-northeast-2)
  - [x] **2.4.1.2** Block Public Access 설정 (모든 공개 액세스 차단 완료)
  - [x] **2.4.1.3** 암호화 설정 (SSE-S3) (AES256 + BucketKey 활성화)
  - [x] **2.4.1.4** CORS 정책 설정 (로컬/Vercel 도메인 허용)
- [x] **2.4.2** CloudFront 배포 설정
  - [x] **2.4.2.1** Origin Access Control (OAC) 생성 (OAC ID: E2L8IJM40TUC0U)
  - [x] **2.4.2.2** 배포 생성 및 Origin 연결 (배포 ID: ESZTOMYA7BE5, 도메인: d3o89byostp1xs.cloudfront.net)
  - [x] **2.4.2.3** Cache Policy 설정 (Range 헤더 허용) (기본 설정에 Range 헤더 포함됨)
  - [x] **2.4.2.4** Signed URL용 키 페어 생성 (공개키 ID: K1MOHSPPL0L417, 키 파일: keys/ 디렉토리에 저장)
    - [x] **키 그룹 생성**: voj-key-group (키 그룹 ID: da9e785e-e204-4932-b474-95e16ba3a350)

---

## 3. 백엔드 개발

### 3.1 API 기본 구조 설정
- [x] **3.1.1** FastAPI 프로젝트 구조 생성
  - [x] **3.1.1.1** 디렉토리 구조 생성 (backend/app/{api,core,models,services,utils})
  - [x] **3.1.1.2** FastAPI 메인 애플리케이션 설정 (main.py)
  - [x] **3.1.1.3** 환경별 설정 관리 (core/config.py)
  - [x] **3.1.1.4** API 라우터 구조 설정 (api/v1/)
  - [x] **3.1.1.5** 기본 엔드포인트 구현 (health, auth, books, audio)
  - [x] **3.1.1.6** Poetry 의존성 관리 (pyproject.toml, email-validator 추가)
  - [x] **3.1.1.7** 로컬 개발 서버 실행 확인 (http://localhost:8000)
- [x] **3.1.2** 환경별 설정 관리 (local/production)
  - [x] **3.1.2.1** 기본 설정 클래스 구조 설계 (BaseAppSettings)
  - [x] **3.1.2.2** 로컬 개발 환경 설정 (LocalSettings)
  - [x] **3.1.2.3** 프로덕션 환경 설정 (ProductionSettings)
  - [x] **3.1.2.4** 설정 팩토리 패턴 구현 (SettingsFactory)
  - [x] **3.1.2.5** 환경별 실행 스크립트 생성 (run-local.sh, run-production.sh)
  - [x] **3.1.2.6** 환경별 설정 문서 작성 (backend/docs/environment-config.md)
  - [x] **3.1.2.7** 설정 검증 및 테스트 (로컬 환경 정상 작동 확인)
- [x] **3.1.3** DynamoDB 연결 설정
  - [x] **3.1.3.1** PynamoDB 기반 기본 모델 클래스 생성 (BaseModel)
  - [x] **3.1.3.2** Book 모델 구현 (사용자별 책 정보, 상태/장르 인덱스)
  - [x] **3.1.3.3** AudioChapter 모델 구현 (챕터 정보, 파일 메타데이터)
  - [x] **3.1.3.4** 데이터베이스 서비스 클래스 구현 (DatabaseService)
  - [x] **3.1.3.5** 헬스 체크 엔드포인트 업데이트 (DynamoDB 상태 확인)
  - [x] **3.1.3.6** 데이터베이스 초기화 엔드포인트 구현 (테이블 생성)
  - [x] **3.1.3.7** 로컬 DynamoDB 연결 및 테이블 생성 테스트 완료
- [x] **3.1.4** S3 클라이언트 설정
  - [x] **3.1.4.1** 스토리지 기본 인터페이스 설계 (BaseStorageService)
  - [x] **3.1.4.2** 로컬 파일 시스템 스토리지 구현 (LocalStorageService)
  - [x] **3.1.4.3** AWS S3 스토리지 구현 (S3StorageService)
  - [x] **3.1.4.4** 스토리지 팩토리 패턴 구현 (환경별 자동 선택)
  - [x] **3.1.4.5** 파일 관리 API 엔드포인트 구현 (업로드, 다운로드, 삭제)
  - [x] **3.1.4.6** Pre-signed URL 지원 (프로덕션 환경)
  - [x] **3.1.4.7** 헬스 체크에 스토리지 상태 확인 추가
  - [x] **3.1.4.8** 로컬 파일 업로드 테스트 완료
- [ ] **3.1.5** Cognito 인증 미들웨어 구현

### 3.2 Books API 구현
- [ ] **3.2.1** 책 생성 API (`POST /books`)
- [ ] **3.2.2** 책 목록 조회 API (`GET /books`)
- [ ] **3.2.3** 책 상세 조회 API (`GET /books/{book_id}`)
- [ ] **3.2.4** 책 수정 API (`PUT /books/{book_id}`)
- [ ] **3.2.5** 책 삭제 API (`DELETE /books/{book_id}`)
- [ ] **3.2.6** 표지 업로드 Presigned URL API (`POST /books/{book_id}/cover:presign`)

### 3.3 Audio API 구현
- [ ] **3.3.1** 오디오 업로드 Presigned URL API (`POST /books/{book_id}/audios:presign`)
- [ ] **3.3.2** 챕터 목록 조회 API (`GET /books/{book_id}/audios`)
- [ ] **3.3.3** 챕터 메타데이터 수정 API (`PUT /books/{book_id}/audios/{audio_id}`)
- [ ] **3.3.4** 챕터 삭제 API (`DELETE /books/{book_id}/audios/{audio_id}`)

### 3.4 스트리밍 API 구현
- [ ] **3.4.1** CloudFront Signed URL 생성 API (`POST /stream/{audio_id}:sign`)
- [ ] **3.4.2** 로컬 환경용 파일 서빙 API 구현

### 3.5 인코딩 파이프라인 구현
- [ ] **3.5.1** FFmpeg Lambda Layer 생성
- [ ] **3.5.2** 인코딩 Lambda 함수 구현
  - [ ] **3.5.2.1** S3 Event 트리거 설정
  - [ ] **3.5.2.2** WAV → AAC 변환 로직
  - [ ] **3.5.2.3** 메타데이터 추출 (ffprobe)
  - [ ] **3.5.2.4** DynamoDB 업데이트
  - [ ] **3.5.2.5** 오류 처리 및 DLQ 설정

---

## 4. 프론트엔드 개발 (어드민)

### 4.1 프로젝트 기본 설정
- [ ] **4.1.1** Next.js 15 (App Router) 프로젝트 생성
- [ ] **4.1.2** TypeScript 설정
- [ ] **4.1.3** Tailwind CSS 설정
- [ ] **4.1.4** Shadcn UI 설정

### 4.2 인증 시스템 구현
- [ ] **4.2.1** Cognito 인증 설정
- [ ] **4.2.2** 로그인 페이지 구현
- [ ] **4.2.3** 인증 상태 관리 (Context/Zustand)
- [ ] **4.2.4** 보호된 라우트 구현

### 4.3 책 관리 기능 구현
- [ ] **4.3.1** 책 목록 페이지 (페이지네이션 포함)
- [ ] **4.3.2** 책 생성/편집 폼
- [ ] **4.3.3** 표지 이미지 업로드 컴포넌트
- [ ] **4.3.4** 책 삭제 기능

### 4.4 오디오 관리 기능 구현
- [ ] **4.4.1** 드래그앤드롭 오디오 업로드 컴포넌트
- [ ] **4.4.2** 업로드 진행 상태 표시
- [ ] **4.4.3** 챕터 순서 변경 (드래그 정렬)
- [ ] **4.4.4** 챕터 미리듣기 기능
- [ ] **4.4.5** 인코딩 상태 표시 (대기/진행/완료/오류)

### 4.5 접근성 및 UX 개선
- [ ] **4.5.1** 키보드 내비게이션 지원
- [ ] **4.5.2** 포커스 링 및 큰 버튼 스타일
- [ ] **4.5.3** 스크린 리더 지원 (ARIA 레이블)

---

## 5. 통합 테스트

### 5.1 단위 테스트
- [ ] **5.1.1** 백엔드 API 단위 테스트 작성
- [ ] **5.1.2** 프론트엔드 컴포넌트 테스트 작성

### 5.2 통합 테스트
- [ ] **5.2.1** 책 CRUD 전체 플로우 테스트
- [ ] **5.2.2** 오디오 업로드 → 인코딩 → 스트리밍 플로우 테스트
- [ ] **5.2.3** 인증 플로우 테스트

### 5.3 성능 테스트
- [ ] **5.3.1** API 응답 시간 측정
- [ ] **5.3.2** 파일 업로드 성능 테스트
- [ ] **5.3.3** 스트리밍 성능 테스트

---

## 6. 배포 및 운영

### 6.1 IaC 구성
- [ ] **6.1.1** CDK 프로젝트 구조 생성
- [ ] **6.1.2** 스택별 리소스 정의
  - [ ] **6.1.2.1** StorageStack (S3 + CloudFront)
  - [ ] **6.1.2.2** DatabaseStack (DynamoDB)
  - [ ] **6.1.2.3** ApiStack (API Gateway + Lambda)
  - [ ] **6.1.2.4** AuthStack (Cognito + IAM)
- [ ] **6.1.3** 환경별 설정 분리 (dev/staging/prod)

### 6.2 배포 스크립트 구성
- [ ] **6.2.1** `scripts/deploy-prod.sh` 스크립트 작성
- [ ] **6.2.2** CI/CD 파이프라인 설정 (GitHub Actions)

### 6.3 모니터링 및 알람 설정
- [ ] **6.3.1** CloudWatch 로그 그룹 생성
- [ ] **6.3.2** 주요 메트릭 알람 설정
  - [ ] **6.3.2.1** Lambda 오류율 알람
  - [ ] **6.3.2.2** CloudFront 5xx 오류 알람
  - [ ] **6.3.2.3** S3 403 오류 알람
- [ ] **6.3.3** 대시보드 구성

### 6.4 보안 및 백업
- [ ] **6.4.1** 보안 정책 검토 및 적용
- [ ] **6.4.2** 데이터 백업 전략 수립
- [ ] **6.4.3** 재해 복구 계획 수립

---

## 7. 개선 사항 백로그

- [ ] **보안/시크릿 관리 개선**
  - [ ] LocalSettings의 Cognito 등 민감정보를 코드에서 제거하고 `.env.local`로 이전
  - [ ] 프로덕션 시크릿(Cognito Client Secret, CloudFront Private Key) 보관소 이전(Secrets Manager/SSM)
  - [ ] 노출 가능성 있는 키 전량 롤테이션 계획 수립 및 실행

- [ ] **DynamoDB 스키마 정합성 확보**
  - [ ] PynamoDB 모델(Book: `user_id`+`book_id`, AudioChapter 스키마) ↔ DynamoDB(Local/Prod) 테이블 스키마 일치화
  - [ ] `scripts/create-local-tables.py`를 모델 스키마 기준으로 수정 또는 PynamoDB로 테이블 생성 일원화
  - [ ] 프로덕션 테이블 영향 분석 및 마이그레이션 계획 수립

- [ ] **파일 URL/스트리밍 경로 일관성**
  - [x] 로컬 URL 생성(`LocalStorageService._get_url`, `audio.get_streaming_url`)을 Files 라우트(`/api/v1/files/...`)와 일치시키기
  - [ ] 미구현 경로(`/storage`, `/local-files`) 제거 또는 `StaticFiles` 마운트로 구현 정합성 확보
  - [x] 프로덕션 기본을 CloudFront Signed URL로 표준화하고 Range 헤더 처리 확인

- [ ] **개발 스크립트/문서 정합성**
  - [ ] `scripts/setup-local.sh` 실행 안내의 uvicorn 대상 수정(`app.main:app`)
  - [ ] README/환경 문서의 실행/테스트 플로우 최신화

- [ ] **의존성 정리**
  - [ ] `python-jose` 사용 여부 확인 후 미사용 시 제거(`pyjwt` 중심으로 통일)
  - [ ] 불필요/중복 패키지 점검 및 제거

- [ ] **테스트 보강**
  - [ ] 인증 디펜던시(`get_current_user_claims`, `require_any_scope`) 단위 테스트 추가
  - [ ] Files API 업로드/다운로드/권한/에러 경로 테스트 추가
  - [ ] 상세 헬스체크(`GET /api/v1/health/detailed`) 테스트 추가

## 📊 진행률 추적

### 현재 진행 상황
```
전체 진행률: 0% (0/59)

1. 개발 환경 구축: 0% (0/8)
2. 인프라 구성: 0% (0/12)
3. 백엔드 개발: 0% (0/15)
4. 프론트엔드 개발: 0% (0/10)
5. 통합 테스트: 0% (0/6)
6. 배포 및 운영: 0% (0/8)
```

### 마일스톤
- [ ] **M1**: 로컬 개발 환경 완료 (1주차)
- [ ] **M2**: AWS 인프라 구성 완료 (2주차)
- [ ] **M3**: 백엔드 API 개발 완료 (4주차)
- [ ] **M4**: 프론트엔드 개발 완료 (6주차)
- [ ] **M5**: 통합 테스트 완료 (7주차)
- [ ] **M6**: 프로덕션 배포 완료 (8주차)

---

## 📝 업데이트 로그

### 2025-09-12
- URL 설계 가이드 추가(로컬/프로덕션), 스트리밍 항목 체크 반영
- 인코딩 파이프라인 5.1 S3→Lambda 트리거 스펙 문서화
- 인코딩 파이프라인 5.2 ffmpeg 변환 스크립트 설계 문서화
- 인코딩 파이프라인 5.3 결과 키 정책 및 메타 업데이트 문서화
- 인코딩 파이프라인 5.4 실패 재시도/에러 로깅/DLQ 설계 문서화
- 인코딩 파이프라인 5.5 Lambda 권한/Layer/IaC 초안 문서화
- 6.1 로컬 테이블 생성 스크립트 PynamoDB 기반 일원화(`scripts/create-local-tables.py`)
- 6.2 프로덕션 테이블↔모델 필드 비교표 및 해소 계획 문서화(`docs/design.md#16`)
- 6.3 마이그레이션/백필 전략(무중단 지향) 문서화(`docs/design.md#16.4`)
- 부모 작업 완료 체크: 3.0/5.0/6.0 완료

### 2024-XX-XX
- 초기 체크리스트 생성
- 워크플로우 기반 계층 구조 설계

---

> 💡 **사용법**: 각 항목을 완료할 때마다 `- [x]`로 체크하고, 진행률을 업데이트하세요.
> 
> 🔄 **업데이트**: 새로운 요구사항이나 변경사항이 있을 때마다 이 체크리스트를 업데이트하세요.