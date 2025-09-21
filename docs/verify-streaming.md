# CloudFront Signed URL 스트리밍 검증 가이드

프로덕션 환경에서 오디오 스트리밍이 정상 동작하는지 확인하는 절차입니다. 배포 체크리스트 9.x 항목을 수행할 때 참고하세요.

## 1. 서명 URL 발급

1. 백엔드 관리자 계정으로 로그인합니다.
2. 책과 챕터가 준비되어 있다면 `/api/v1/audio/{book_id}/{chapter_id}/stream` API를 호출하여 `signed_url`을 획득합니다.
   - cURL 예시:
     ```bash
     curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
       "https://api.voj-audiobook.com/api/v1/audio/<book_id>/<chapter_id>/stream"
     ```
3. 응답에서 `url` 또는 `signed_url` 필드를 복사합니다.

## 2. Range 요청 확인 (9.3)

`SIGNED_URL` 환경 변수에 위에서 복사한 URL을 설정한 뒤 스크립트를 실행합니다.

```bash
SIGNED_URL="<서명URL>" ./scripts/check-streaming.sh
```

- 기대 결과: HTTP 206 Partial Content, `Content-Range: bytes 0-127/...` 헤더, 최소 1바이트 이상 수신
- 실패 시 확인:
  - CloudFront 배포의 Cache 정책에 `Range` 헤더가 허용되어 있는지
  - CloudFront → S3 원본 접근 권한(OAC)이 유효한지
  - 서명 URL의 만료 시간이 지나지 않았는지

## 3. 전체 다운로드 확인 (선택)

```bash
curl -L "<서명URL>" -o chapter.m4a
```

파일을 로컬에서 재생해 문제가 없는지 확인합니다.

## 4. 직접 S3 접근 차단 검증 (9.4)

사전 준비: S3 객체 키를 알고 있어야 합니다(예: `book/<book_id>/media/0001.m4a`).

```bash
aws s3 presign s3://voj-audiobooks-prod/book/<book_id>/media/0001.m4a --expires-in 60
```

- 서명 URL이 403을 반환해야 하며, CloudFront를 통한 접근만 허용되어야 합니다.
- 만약 다운로드가 가능하다면 S3 버킷 정책과 OAC 설정을 재검토하세요.

## 5. TTL 및 도메인 확인 (9.2)

- 서명 URL의 만료 시간이 요구사항에 맞는지 확인합니다(예: 10분).
- URL이 `https://d3o89byostp1xs.cloudfront.net/...` 또는 커스텀 도메인을 사용하고 있는지 확인합니다.
- CloudFront 키 페어와 키 그룹이 최신 상태인지 점검합니다.

## 6. 문제 해결 체크리스트

- 401/403: Access Token 만료 또는 CloudFront 서명 오류
- 502/504: Lambda/API Gateway 응답 지연 → CloudWatch Logs 확인
- 200(Partial 아님): 원본에서 Range를 지원하지 않는 경우 → S3 기본 설정, Lambda 응답 헤더 확인

검증이 완료되면 `tasks/tasks-prd-audiobook-mvp-v2-deploy.md`의 9.x 항목을 업데이트하세요.
