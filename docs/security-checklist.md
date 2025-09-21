# 프로덕션 보안 점검 체크리스트

체크리스트 11.x 항목을 수행할 때 참고하세요.

## 1. CORS 정책 (11.1)

- [ ] 백엔드 `ALLOWED_HOSTS` 환경 변수에 다음 도메인이 포함되어 있는지 확인
  - 프론트엔드: Amplify 기본 도메인 및 커스텀 도메인 (예: `https://main.dxxx.amplifyapp.com`)
  - CloudFront: `https://d3o89byostp1xs.cloudfront.net` 또는 커스텀 도메인
  - API Gateway: `https://api.voj-audiobook.com`
- [ ] API Gateway Stage 설정에서 CORS가 활성화되어 있는지 확인
- [ ] CloudFront 배포의 Response Headers Policy에 필요한 CORS 헤더가 포함되어 있는지 검토

## 2. TrustedHostMiddleware (11.2)

- [ ] `backend/app/core/settings/production.py` 의 `ALLOWED_HOSTS`에 프로덕션 도메인이 반영되었는지 확인
- [ ] Lambda 환경 변수에서 `API_GATEWAY_URL`, `CLOUDFRONT_DOMAIN`이 최신 값인지 검증

## 3. 키/시크릿 보관 (11.3)

- [ ] CloudFront 개인키는 AWS Secrets Manager 또는 SSM Parameter Store(`CLOUDFRONT_PRIVATE_KEY_SECRET_ID`)에 저장되어 있는지 확인
- [ ] Lambda IAM 역할에 해당 시크릿에 대한 읽기 권한만 부여되었는지 확인 (정책 제한)
- [ ] `SIMPLE_AUTH_*` 자격증명도 Secrets Manager/SSM에 보관하고 Lambda 환경 변수는 런타임에 주입

## 4. S3 Public Access 차단 및 OAC (11.4)

- [ ] `voj-audiobooks-prod` 버킷의 Block Public Access가 모두 `ON`인지 확인
- [ ] 버킷 정책이 CloudFront Origin Access Control(OAC)만 접근하도록 제한되어 있는지 검토
- [ ] CloudFront 배포의 Origin이 해당 OAC를 사용하고 있는지 확인
- [ ] IAM 사용자/역할에 직접 S3 객체 읽기 권한을 부여하지 않았는지 재검토

## 5. 추가 점검

- [ ] Lambda IAM 역할 최소 권한 원칙 준수 (DynamoDB/S3/CloudWatch Logs 등 필요한 리소스만)
- [ ] API Gateway 리소스 정책으로 지정 IP/역할 제한이 필요한지 검토
- [ ] CloudFront Signed URL TTL/경로 제한이 요구 사항에 맞는지 재확인
- [ ] CloudWatch Logs에 민감 정보가 기록되지 않도록 필터링

## 6. 증적(권장)

- 점검 완료 후 해당 설정 스크린샷 혹은 CLI 결과를 보관
- 문제 발생 시 롤백/수정 이력 관리를 위해 Notion/위키에 기록

필요 시 `docs/rollout-plan.md`, `docs/monitoring.md` 와 연동해 배포/모니터링 흐름 속에서 보안 점검을 수행하세요.
