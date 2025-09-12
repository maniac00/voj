## Relevant Files

- `docs/prd.md` - 제품 요구사항 문서(PRD) 원본.
- `backend/app/main.py` - FastAPI 엔트리포인트 및 전역 미들웨어 설정.
- `backend/app/api/v1/api.py` - v1 라우터 집결점.
- `backend/app/api/v1/endpoints/` - 현재 엔드포인트(health, auth, books, audio, files) 모음.
- `backend/app/core/settings/*` - 환경별 설정(Local/Production), 시크릿/리소스 설정 위치.
- `backend/app/core/auth/*` - JWT 검증 및 인증 디펜던시.
- `backend/app/models/*` - PynamoDB 모델(Book, AudioChapter).
- `backend/app/services/storage/*` - 스토리지 추상화(Local/S3/CloudFront).
- `backend/app/services/database.py` - DynamoDB 테이블 초기화/헬스체크.
- `docker-compose.yml` - 로컬 DynamoDB/관리 UI 구성.
- `scripts/create-local-tables.py` - 로컬 테이블 생성 스크립트(스키마 정합성 확인 필요).
- `backend/docs/environment-config.md` - 환경 설정 문서.
- `docs/checklist.md` - 상위 진행 체크리스트.
- `src/lib/auth/amplify-config.ts` - 프론트엔드 Amplify 설정 유틸(환경 변수 기반).
- `backend/app/services/books.py` - Book 도메인 서비스 계층(CRUD/목록/페이지네이션).
- `tests/test_books_service.py` - BookService 단위 테스트.
 - `backend/app/utils/ffprobe.py` - ffprobe 기반 오디오 메타데이터 추출 유틸.
 - `tests/test_ffprobe_utils.py` - ffprobe 유틸 테스트(ffmpeg/ffprobe 존재 시 실행).
 - `tests/test_storage_key_policy.py` - 스토리지 키 정책 표준화 테스트.
 - `tests/test_files_upload.py` - 파일 업로드 검증(권한/사이즈/타입/키 형식) 테스트.
 - `tests/test_audio_list_chapters.py` - 실제 데이터 기반 챕터 목록 테스트.
 - `tests/test_audio_reorder_chapter.py` - 챕터 순서 변경 API 테스트.
 - `tests/test_audio_delete_chapter.py` - 챕터 삭제 API 테스트(스토리지 정리 포함).
 - `tests/test_audio_end_to_end_flow.py` - Audio 업로드→목록→정렬→삭제 E2E 테스트.
 - `tests/test_audio_streaming_signed_url.py` - CloudFront Signed URL 스트리밍 테스트.
 - `tests/test_files_range_requests.py` - 로컬 파일 Range 요청(부분 스트리밍) 테스트.
 - `backend/app/utils/ffprobe.py` - ffprobe 기반 오디오 메타데이터 추출 유틸.
 - `tests/test_ffprobe_utils.py` - ffprobe 유틸 테스트(ffmpeg/ffprobe 존재 시 실행).
 - `tests/test_storage_key_policy.py` - 스토리지 키 정책 표준화 테스트.
 - `tests/test_files_upload.py` - 파일 업로드 검증(권한/사이즈/타입/키 형식) 테스트.
 - `tests/test_audio_list_chapters.py` - 실제 데이터 기반 챕터 목록 테스트.
 - `tests/test_audio_reorder_chapter.py` - 챕터 순서 변경 API 테스트.
 - `tests/test_audio_delete_chapter.py` - 챕터 삭제 API 테스트(스토리지 정리 포함).
 - `tests/test_audio_end_to_end_flow.py` - Audio 업로드→목록→정렬→삭제 E2E 테스트.
- `tests/test_books_endpoint_post.py` - POST /books 엔드포인트 테스트.
- `tests/test_books_endpoint_list.py` - GET /books 목록/필터/검색 테스트.
- `tests/test_books_endpoint_get_one.py` - GET /books/{book_id} 소유권 테스트.
- `tests/test_books_endpoint_put.py` - PUT /books/{book_id} 부분 업데이트 테스트.
- `tests/test_books_endpoint_delete.py` - DELETE /books/{book_id} 삭제 테스트.
- `tests/test_books_end_to_end.py` - Book API E2E 플로우 테스트.
- `tests/` - 백엔드 테스트 루트 디렉터리(추가 예정 테스트 배치).
- `env.local.example` - 로컬 환경 변수 템플릿(시크릿 비워두기, Cognito BYPASS 주석 포함).
- `backend/app/core/settings/local.py` - 로컬 설정(Cognito 하드코딩 제거, env 로드).
- `backend/app/api/v1/endpoints/health.py` - 상세 헬스체크에 Cognito 설정 경고 추가.
- `backend/docs/environment-config.md` - 환경 변수 섹션에 Cognito 안내 보강.
- `docs/design.md` - 시크릿 관리 원칙 및 URL 설계 가이드 추가.
- `tests/test_auth_jwt.py` - Cognito JWT 검증 테스트(예외/시간초과/키 회전 포함).
- `tests/test_auth_deps.py` - 로컬 바이패스/스코프/그룹 처리 테스트.
- `tests/test_auth_endpoints.py` - 로그인/로그아웃/내 정보(me) 로컬 BYPASS 동작 테스트.
- `tests/test_auth_scopes.py` - 스코프 추출/검증 유틸 및 요구 스코프 동작 테스트.

### Notes

- 단위 테스트 파일은 해당 코드 파일과 같은 디렉토리에 배치합니다(e.g., `foo.py`와 `test_foo.py`).
- 백엔드는 pytest를 사용하며, `poetry run pytest`로 실행합니다.
- 프론트엔드는 jest를 사용하며, `npm run test`로 실행합니다.

## Tasks

- [x] 1.0 인증/권한 기반 어드민 로그인 흐름 확정(Cognito)
  - [x] 1.1 Cognito User Pool/Client 환경 변수로 분리(.env, Secrets Manager 계획)
  - [x] 1.2 `verify_cognito_jwt` 예외/시간초과/키회전 대응 강화 테스트
  - [x] 1.3 `get_current_user_claims` 로컬 바이패스 명확화 및 스코프 정책 합의
  - [x] 1.4 로그인/로그아웃 엔드포인트 실제 구현(임시 더미 제거)
  - [x] 1.5 권한 스코프 매핑 표준화(`require_any_scope` 테스트 포함)
  - [x] 1.6 프론트엔드 Amplify(or auth SDK) 설정 초안

- [x] 2.0 Book 관리 API 완성(등록/수정/삭제/조회 + 페이지네이션)
  - [x] 2.1 PynamoDB Book 모델 기반 CRUD 서비스 계층 추가
  - [x] 2.2 `POST /api/v1/books` 구현 + 입력 검증 + 소유권 부여
  - [x] 2.3 `GET /api/v1/books` 페이지네이션/필터(status, genre, search)
  - [x] 2.4 `GET /api/v1/books/{book_id}` 권한/소유 검증
  - [x] 2.5 `PUT /api/v1/books/{book_id}` 부분 업데이트
  - [x] 2.6 `DELETE /api/v1/books/{book_id}` 연관 리소스 정리 정책
  - [x] 2.7 단위/통합 테스트(pytest) 작성

- [ ] 3.0 Audio 관리 API 완성(업로드/메타데이터/순서 관리/삭제)
  - [x] 3.1 업로드 경로 키 정책 확정(`generate_key` 표준화)
  - [x] 3.2 `POST /api/v1/files/upload` 권한/사이즈/타입 검증 강화
  - [x] 3.3 `GET /api/v1/audio/{book_id}/chapters` 실제 데이터 반환
  - [x] 3.4 순서 변경 API 설계(`PUT /api/v1/audio/{book_id}/chapters/{id}`)
  - [x] 3.5 삭제 API 정합성(`DELETE ...`) + 스토리지 삭제
  - [x] 3.6 ffprobe 메타데이터 추출 로직(Lambda 전 단계) 유틸 추가
  - [x] 3.7 테스트(업로드→목록→정렬→삭제 흐름)

- [x] 4.0 스트리밍 제공 방식 확정 및 구현(CloudFront Signed URL, Range)
  - [x] 4.1 로컬: Files 경유 스트리밍 일원화(`/api/v1/files/{file_key}`)
  - [x] 4.2 프로덕션: CloudFront Signed URL 표준화 및 만료정책 문서화
  - [x] 4.3 Range 헤더 처리 확인 및 E2E 테스트(진행바 탐색)
  - [x] 4.4 URL 설계 가이드 문서화(로컬/프로덕션 동작 차이)

- [ ] 5.0 인코딩 파이프라인 설계 및 MVP 구현(S3 이벤트 → Lambda ffmpeg)
  - [x] 5.1 S3 Event → Lambda 트리거 스펙 초안
  - [ ] 5.2 ffmpeg 변환 스크립트 설계(AAC/Opus 중 택1, 메타 수집)
  - [ ] 5.3 결과 파일 키 정책(media/) 및 메타 업데이트
  - [ ] 5.4 실패 재시도/에러 로깅/DLQ 설계
  - [ ] 5.5 Lambda 권한/Layer/IaC 초안

- [ ] 6.0 데이터 모델/테이블 스키마 정합성 확립(로컬/프로덕션)
  - [ ] 6.1 로컬 테이블 생성 방식을 PynamoDB `create_table`로 일원화 또는 boto3 스크립트 수정
  - [ ] 6.2 프로덕션 테이블과 모델 필드 비교표 작성 및 차이 해소 계획
  - [ ] 6.3 마이그레이션/백필 전략(필요 시) 수립

- [ ] 7.0 프론트엔드 어드민 기본 UI 프레임(로그인/책/오디오 관리)
  - [ ] 7.1 Next.js 15 App Router 스캐폴딩(TypeScript, Tailwind, Shadcn)
  - [ ] 7.2 로그인 화면 + Cognito 연동(Amplify/SDK)
  - [ ] 7.3 책 목록/등록/편집/삭제 페이지
  - [ ] 7.4 오디오 업로드(DnD) + 진행률/정렬 UI
  - [ ] 7.5 접근성 기본(키보드/ARIA/포커스)

- [ ] 8.0 보안/시크릿/권한 정책 강화(시크릿 분리, 최소권한)
  - [ ] 8.1 코드 내 시크릿 제거 → `.env`/AWS Secrets Manager로 이전
  - [ ] 8.2 IAM 최소권한 정책 검토/수정
  - [ ] 8.3 감사/로그 정책 문서화

- [ ] 9.0 테스트 전략 수립 및 핵심 시나리오 TDD(백엔드/프론트엔드)
  - [ ] 9.1 백엔드 단위/통합 테스트 스캐폴딩(pytest-asyncio 포함)
  - [ ] 9.2 인증/파일/헬스체크 주요 경로 커버리지 목표 설정
  - [ ] 9.3 프론트엔드 컴포넌트 테스트(Jest/RTL) 기초

- [ ] 10.0 배포 파이프라인 및 운영 가이드(로그/알람)
  - [ ] 10.1 GitHub Actions CI(테스트/린트) → CD(배포) 초안
  - [ ] 10.2 CloudWatch 로그/알람(5xx, S3 403, Lambda 오류)
  - [ ] 10.3 운영 가이드/Runbook 작성


