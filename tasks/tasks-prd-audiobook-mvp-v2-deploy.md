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

- [ ] 1.0 배포 범위/전제 확정 (MVP v2, 리전/도메인/네트워크)
- [ ] 2.0 IAM/권한 준비 (역할/정책/키)
- [ ] 3.0 S3 버킷 생성 및 CORS/암호화/퍼블릭 차단 설정
- [ ] 4.0 CloudFront 배포(OAC)/키 그룹/서명 키 생성 및 정책 연결
- [ ] 5.0 DynamoDB 프로덕션 테이블 준비(Books, AudioChapters)
- [ ] 6.0 백엔드 배포 전략 수립(API Gateway + Lambda)
- [ ] 7.0 백엔드 패키징/배포 구성(환경 변수/시크릿/ALLOWED_HOSTS/CORS)
- [ ] 8.0 프론트엔드 배포(Amplify 또는 Vercel) 및 환경 변수 주입
- [ ] 9.0 서명 URL/스트리밍 정책 검증(CloudFront, Range, TTL)
- [ ] 10.0 모니터링/로깅/알람(CloudWatch, CF/S3 지표, 5xx/403 경보)
- [ ] 11.0 보안 점검(CORS/TrustedHost/키 보관/원본 접근 차단)
- [ ] 12.0 프로덕션 스모크 테스트(로그인→책 생성→.m4a 업로드→재생/Range)
- [ ] 13.0 롤백/재배포 전략 수립 및 문서화
