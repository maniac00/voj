## Relevant Files

- `backend/app/core/settings/production.py` - 프로덕션 환경 변수/설정 로딩 (도메인, 버킷, 리전, CF 키 등)
- `backend/app/core/config.py` - 환경 분기/설정 진입점(ENVIRONMENT, ALLOWED_HOSTS)
- `backend/app/api/v1/endpoints/files.py` - 업로드/다운로드 경로, 프로덕션에서 S3 프리사인드/직접 경로 사용
- `backend/app/api/v1/endpoints/audio.py` - 스트리밍 URL 생성(Production: CloudFront Signed URL 우선)
- `backend/app/services/storage/s3.py` - S3 업/다운로드/프리사인드 URL 생성(프로덕션 핵심)
- `backend/app/services/storage/local.py` - 로컬 대비 동작 참고(프로덕션 분기 확인)
- `backend/app/services/storage/factory.py` - 환경별 스토리지 서비스 선택(Production=S3)
- `backend/app/main.py` - CORS/TrustedHost, 프로덕션 문서 비공개, Lifespan 전환 TODO
- `aws-policies/*.json` - IAM 정책 정의(버킷/S3/CloudFront/DynamoDB/Lambda 권한)
- `scripts/setup-aws-permissions.sh` - AWS 권한/정책 셋업 스크립트
- `scripts/create-cloudfront-keygroup.sh` - CloudFront Key Group 생성(서명 URL용)
- `scripts/add-cloudfront-permissions.sh` - CF 키 권한/정책 연결
- `scripts/create-lambda-roles.sh` / `scripts/attach-lambda-policies.sh` - Lambda 실행 역할 및 정책 연결
- `frontend/next.config.js` - 도메인/이미지/압축 설정(필요 시)
- `frontend/src/lib/api.ts` - API_BASE 절대 경로(Prod: API Gateway 도메인)
- `frontend/src/lib/audio.ts` - 스트리밍 URL API 호출(Prod 대응)
- `docs/design.md` - URL/서명 정책, 파일명/키 정규화(15.x)
- `docs/checklist.md` - 배포 체크/로그 업데이트 장소

### Notes

- Unit tests는 백엔드 pytest 중심, 배포 전 스모크를 우선 수행합니다.
- 배포 타깃: AWS (API: API Gateway + Lambda, 데이터: DynamoDB, 스토리지: S3, CDN: CloudFront)
- MVP v2 제약: ENCODING_ENABLED=False, 업로드는 .mp4/.m4a만 허용, 업로드 즉시 ready, 로컬/Prod 동작 차이는 스트리밍 URL 생성에만 반영
- 시크릿: CloudFront 키 페어, 버킷명, 테이블명, API 도메인, 토큰 시드 등은 SSM/Secrets Manager로 관리

## Tasks

- [x] 1.0 배포 범위/전제 확정 (MVP v2, 리전/도메인/네트워크)
  - [x] 1.1 배포 리전 확정 및 공통 변수 수집 (예: ap-northeast-2)
  - [x] 1.2 도메인/엔드포인트 확정 (API Gateway 도메인, CloudFront 도메인)
  - [x] 1.3 버킷/테이블/스택 네이밍 규칙 확정 (`voj-audiobooks-prod`, `voj-books-prod`, `voj-audio-chapters-prod`)
  - [x] 1.4 프로덕션 설정에서 `ENCODING_ENABLED=False` 확인 및 문서화
  - [x] 1.5 배포용 시크릿 키 목록 정리 (CF KeyPair, 테이블/버킷명, API URL)

- [x] 2.0 IAM/권한 준비 (역할/정책/키)
  - [x] 2.1 AWS CLI 프로파일/자격 확인 (`aws sts get-caller-identity`)
  - [x] 2.2 Lambda(API) 실행 역할 생성 및 신뢰 정책 연결
  - [x] 2.3 정책 연결: S3(read uploads/ put media/), DynamoDB(Books/AudioChapters CRUD), Logs
  - [x] 2.4 CloudFront Key Group/Key Pair 준비(공개키/개인키), 키 관리 전략(Secrets Manager/SSM)
  - [x] 2.5 스크립트 실행 검토: `scripts/setup-aws-permissions.sh`, `create-lambda-roles.sh`, `attach-lambda-policies.sh`, `add-cloudfront-permissions.sh`
  - [x] 2.6 최소 권한 점검(권한 스코프/리소스 ARN 범위 축소)


- [ ] 3.0 S3 버킷 생성 및 CORS/암호화/퍼블릭 차단 설정
  - [x] 3.1 버킷 생성(비공개, 리전 일치)
  - [x] 3.2 Block Public Access=ON, 기본 암호화=SSE-S3
  - [x] 3.3 CORS 정책 적용(GET/HEAD, Range, 최소 Origin)
  - [x] 3.4 OAC 연동 대비 버킷 정책 점검(직접 퍼블릭 접근 차단)
  - [x] 3.5 수명주기/버전관리 여부 결정(선택)

- [ ] 4.0 CloudFront 배포(OAC)/키 그룹/서명 키 생성 및 정책 연결
  - [ ] 4.1 배포 생성(S3 Origin+OAC), 기본 동작에 Range 허용 캐시 정책 연결
  - [ ] 4.2 Key Group 생성 및 공개키 등록, 배포에 서명 정책 연결
  - [ ] 4.3 개인키 보관(Secrets Manager/Parameter Store) 및 애플리케이션에서 접근 경로 확정
  - [ ] 4.4 배포 도메인 확보, 캐시 정책/오류 응답 정책 최적화
  - [ ] 4.5 Invalidation 전략/스크립트 마련

- [ ] 5.0 DynamoDB 프로덕션 테이블 준비(Books, AudioChapters)
  - [ ] 5.1 테이블 생성(스루풋/온디맨드 결정), 파티션키/인덱스 정책 확정
  - [ ] 5.2 Books 테이블 생성 및 인덱스(필요 시)
  - [ ] 5.3 AudioChapters 테이블 생성 및 GSI 구성(문서 기준)
  - [ ] 5.4 테이블 이름 환경별 접미사/프리픽스 규칙 반영
  - [ ] 5.5 헬스/권한 점검(읽기/쓰기)

- [ ] 6.0 백엔드 배포 전략 수립(API Gateway + Lambda)
  - [ ] 6.1 Lambda 패키징 방식 확정(zip vs 컨테이너)
  - [ ] 6.2 API Gateway(HTTP API) → Lambda 프록시 통합 설계
  - [ ] 6.3 Stage/도메인/리소스 정책, CORS 정책 정의
  - [ ] 6.4 경로 매핑 및 헬스/모니터링 엔드포인트 노출 전략

- [ ] 7.0 백엔드 패키징/배포 구성(환경 변수/시크릿/ALLOWED_HOSTS/CORS)
  - [ ] 7.1 의존성 빌드/번들(zip)에 포함(Python deps)
  - [ ] 7.2 환경 변수 주입: ENVIRONMENT=production, 테이블/버킷/리전, CF 키/도메인
  - [ ] 7.3 ALLOWED_HOSTS/CORS 도메인 설정(API/Vercel/앱 도메인)
  - [ ] 7.4 Lambda 배포 및 API Gateway 통합, Stage 배포
  - [ ] 7.5 `GET /api/v1/health/detailed` 프로덕션 응답 확인

- [ ] 8.0 프론트엔드 배포(Amplify 또는 Vercel) 및 환경 변수 주입
  - [ ] 8.1 배포 대상 선택(Vercel 권장 or Amplify)
  - [ ] 8.2 환경 변수 설정: `NEXT_PUBLIC_API_URL`(API Gateway URL)
  - [ ] 8.3 프로덕션 빌드 및 배포, 도메인 연결(선택)
  - [ ] 8.4 인증/리다이렉트 정상 동작 확인(`/login → /dashboard`)

- [ ] 9.0 서명 URL/스트리밍 정책 검증(CloudFront, Range, TTL)
  - [ ] 9.1 책 생성 → `.m4a` 업로드 → 스트리밍 URL 발급 확인
  - [ ] 9.2 CloudFront 서명 URL TTL/도메인/권한 확인
  - [ ] 9.3 Range 요청(206) 수신/Content-Range 헤더 확인(curl 테스트)
  - [ ] 9.4 직접 S3 액세스 차단(OAC) 검증

- [ ] 10.0 모니터링/로깅/알람(CloudWatch, CF/S3 지표, 5xx/403 경보)
  - [ ] 10.1 Lambda Error/Duration/Throttle 알람
  - [ ] 10.2 API Gateway 5xx/4xx, 지연 알람(필요 시)
  - [ ] 10.3 CloudFront 5xx/오리진 에러 비율 알람
  - [ ] 10.4 S3 403 비율/요청 수 모니터링
  - [ ] 10.5 로그 보존 기간 설정 및 비용 점검

- [ ] 11.0 보안 점검(CORS/TrustedHost/키 보관/원본 접근 차단)
  - [ ] 11.1 CORS 정책 점검(최소 Origin/헤더/메서드)
  - [ ] 11.2 TrustedHostMiddleware에 프로덕션 도메인 반영
  - [ ] 11.3 CF 개인키/시크릿 저장소 이관(Secrets Manager/SSM), 권한 최소화
  - [ ] 11.4 S3 Public Access 차단/OAC 정책 재확인

- [ ] 12.0 프로덕션 스모크 테스트(로그인→책 생성→.m4a 업로드→재생/Range)
  - [ ] 12.1 `/auth/login` → `/auth/me` 세션/토큰 확인
  - [ ] 12.2 책 생성 → `.m4a` 업로드(100MB 이하) → 챕터 상태 ready
  - [ ] 12.3 스트리밍 URL 발급 → 플레이어 재생 확인
  - [ ] 12.4 curl Range 0-127 바이트 요청 → 206 응답 확인

- [ ] 13.0 롤백/재배포 전략 수립 및 문서화
  - [ ] 13.1 Lambda 버전/에일리어스 전략 수립 및 이전 버전 보관
  - [ ] 13.2 API Gateway Stage 롤백 절차 문서화
  - [ ] 13.3 CloudFront 무효화/배포 롤백 절차 수립
  - [ ] 13.4 프론트엔드 정적 자산 버전닝/롤백 계획
