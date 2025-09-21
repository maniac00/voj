# 프로덕션 스모크 테스트 시나리오

배포 완료 후 최소한의 기능이 정상 동작하는지 확인하기 위한 체크리스트입니다. 배포 체크리스트 12.x 항목을 진행할 때 참고하세요.

## 준비물

- 관리자 계정 자격증명 (username/password)
- 최신 Access Token (필요 시 `/api/v1/auth/login`으로 발급)
- 테스트용 `.m4a` 오디오 파일 (100MB 이하)

## 1. 인증 플로우 (12.1)

1. 브라우저에서 프런트엔드 도메인 접속 (예: Amplify 배포 도메인)
2. `/login` 페이지에서 관리자 계정으로 로그인
3. 로그인 성공 후 대시보드로 리디렉션되는지 확인 (`/dashboard` 또는 `/books`)
4. 브라우저 개발자 도구 → Network 탭에서 `/api/v1/auth/me` 호출이 200 OK인지 확인

## 2. 책 생성 및 목록 확인 (12.2 일부)

1. `새 책 추가` 버튼 클릭
2. 제목, 저자 등 필수 필드를 입력하고 저장
3. 목록에 새 책이 표시되는지 확인

## 3. 오디오 업로드 및 상태 확인 (12.2, 12.3)

1. 방금 생성한 책 상세 페이지 진입
2. 오디오 업로드 폼에서 `.m4a` 파일 선택 후 업로드
3. 업로드 완료 후 챕터 상태가 `ready`로 표시되는지 확인
4. 백엔드 로그 혹은 DynamoDB 테이블에서 챕터 메타데이터 생성 확인 (선택)

## 4. 스트리밍 URL 발급 및 재생 (12.3)

1. 업로드 완료된 챕터에서 "재생" 버튼 클릭 또는 `Get streaming URL` 기능 실행
2. 브라우저 내장 플레이어가 재생을 시작하는지 확인
3. 별도의 검증이 필요하면 `docs/verify-streaming.md`의 절차를 따라 `scripts/check-streaming.sh`로 Range 응답(206)과 `Content-Range` 헤더를 확인

## 5. curl Range 요청 (12.4)

```bash
SIGNED_URL="<스트리밍URL>" ./scripts/check-streaming.sh
```

- `HTTP 상태: 206`, `Content-Range` 헤더, 수신 바이트 > 0 을 확인합니다.

## 6. 모니터링/알람 확인

- CloudWatch 대시보드에서 Lambda/API Gateway/CloudFront 지표가 정상인지 확인
- 알람 SNS Topic에 경보가 발생하지 않는지 확인

## 7. 문제 발생 시

- 인증 실패: 백엔드 `SIMPLE_AUTH_*` 값과 프런트 `.env.production` 변수 확인
- 업로드 실패: S3 권한 또는 CORS 설정 확인, Lambda CloudWatch 로그에서 에러 조회
- 스트리밍 실패: CloudFront Signed URL 만료/권한, `ALLOWED_HOSTS` 설정 재검토

테스트가 완료되면 `tasks/tasks-prd-audiobook-mvp-v2-deploy.md`의 12.x 항목을 체크하고 결과를 기록하세요.
