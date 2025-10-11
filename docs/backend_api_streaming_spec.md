# VOJ 실시간 스트리밍 백엔드 API 스펙

> 최신 스키마·요청/응답 형식은 Swagger 문서에서 직접 확인하세요: [`https://voj-production.up.railway.app/api/v1/docs`](https://voj-production.up.railway.app/api/v1/docs)

## 1. 개요
- **목표**: Flutter 기반 시각장애인용 스트리밍 앱에서 백엔드와 안정적으로 연동할 수 있도록 API 계약, 인증, 실시간 채널 요구사항을 정리합니다.
- **주요 기능**: 사용자 인증, 책·오디오 챕터 관리, 파일 업로드, 스트리밍 URL 발급, 로그/상태 WebSocket, 헬스 체크.
- **응답 기본값**: 모든 엔드포인트는 `application/json`(파일 스트림 제외)과 UTF-8을 사용합니다.
- **시간 형식**: ISO-8601 (`2024-05-01T09:00:00Z`).
- **금지 사항**: `/docs` 경로와 Live Swagger는 운영 중이라도 베어러 토큰을 요구하지 않지만, 앱에서의 자동 접속은 금지하고 개발 장비에서만 사용합니다.

## 2. 환경 및 베이스 URL

| 환경 | 베이스 URL | 비고 |
| --- | --- | --- |
| 로컬 개발 | `http://localhost:8080/api/v1` | `poetry run python -m app.main` 실행 후 접근 |
| 스테이징/프로덕션 | `https://voj-production.up.railway.app/api/v1` | Railway 기본 배포 URL. 맞춤 도메인 적용 시 동일 패턴 |

> **참고**: 모든 REST 경로는 위 베이스 URL을 접두사로 사용합니다. 예) 책 목록 조회 → `GET https://voj-production.up.railway.app/api/v1/books`

## 3. 인증 흐름

### 3.1 로그인 · 토큰 발급

- **엔드포인트**: `POST /auth/login`
- **본문(JSON)**:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- **성공 응답**:
  ```json
  {
    "access_token": "<토큰>",
    "token_type": "bearer",
    "expires_in": 86400,
    "username": "admin"
  }
  ```
- **Flutter 팁**: `dio` 인터셉터를 사용해 `Authorization: Bearer <토큰>`을 자동 첨부하세요. 401 수신 시 재로그인 트리거.

### 3.2 현재 사용자 확인
- **엔드포인트**: `GET /auth/me`
- **헤더**: `Authorization: Bearer <토큰>`
- **성공 응답**: `{ "sub": "simple-user-admin", "username": "admin", "scope": "admin" }`

### 3.3 로그아웃
- **엔드포인트**: `POST /auth/logout`
- **상태**: 호출 즉시 200 반환(서버 세션 없음). 클라이언트에서 토큰 삭제 필요.

### 3.4 로컬 개발 바이패스
- `settings.ENVIRONMENT == "local"`이고 헤더가 없으면 서버에서 자동으로 내부 계정을 부여합니다.
- **실제 앱 빌드에서는 항상 로그인 후 토큰을 사용**해야 합니다.

## 4. 공통 요청 규칙
- **헤더**: `Content-Type: application/json`, `Accept: application/json`, 인증이 필요한 경우 `Authorization: Bearer <토큰>`.
- **에러 포맷**: `{ "detail": "에러 메시지" }`. 403/404 시에도 동일 구조.
- **시간대**: 서버는 UTC 저장, 응답은 ISO-8601.
- **파일 업로드 크기 제한**: 100 MB.
- **권한 요구**: `require_any_scope(["admin", "editor"])`가 설정된 엔드포인트는 현재 토큰 스코프가 `admin`인 경우만 허용됩니다.

## 5. 엔드포인트 요약

### 5.1 헬스 체크

| 메서드 | 경로 | 설명 | 인증 |
| --- | --- | --- | --- |
| GET | `/health` | 단순 상태 확인 | 불필요 |
| GET | `/health/detailed` | DB·스토리지·환경 상세 점검 | 불필요 |
| POST | `/health/init-database` | 로컬에서 테이블 생성 | 불필요(로컬만 허용) |
| GET | `/health/environment` | 환경 감지 결과 | 불필요 |
| POST | `/health/environment/auto-configure` | 로컬 디렉터리 자동 구성 | 불필요(로컬만 허용) |

### 5.2 인증

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| POST | `/auth/login` | 토큰 발급 |
| POST | `/auth/logout` | 세션 종료 응답 |
| GET | `/auth/me` | 토큰 검증 및 기본 정보 조회 |

### 5.3 책(Book) 관리

| 메서드 | 경로 | 설명 | 요구 헤더 |
| --- | --- | --- | --- |
| POST | `/books` | 책 생성 | `Authorization` (admin) |
| GET | `/books` | 책 목록 조회 (`page`, `size`, `status`, `genre`, `search`) | `Authorization` |
| GET | `/books/{book_id}` | 책 상세 | `Authorization` |
| PUT | `/books/{book_id}` | 책 정보 수정 | `Authorization` |
| DELETE | `/books/{book_id}` | 책 삭제 | `Authorization` |

> **모든 Book 요청은 해당 토큰 사용자(소유자)의 데이터만 응답합니다. 타 사용자 리소스는 404로 마스킹됩니다.**

### 5.4 오디오 챕터 관리

| 메서드 | 경로 | 설명 | 비고 |
| --- | --- | --- | --- |
| GET | `/audio/{book_id}/chapters` | 해당 책의 챕터 목록 | `status` 쿼리 가능 |
| GET | `/audio/{book_id}/chapters/{chapter_id}` | 챕터 상세 | 404 시 권한 또는 ID 오류 |
| PUT | `/audio/{book_id}/chapters/{chapter_id}?new_number={n}` | 챕터 순서 변경 | `new_number` 필수 |
| DELETE | `/audio/{book_id}/chapters/{chapter_id}` | 챕터 및 파일 삭제 | 성공 시 `{ "message": ... }` |
| GET | `/audio/{book_id}/chapters/{chapter_id}/stream` | 스트리밍 URL 발급 | 응답에 상대 경로 포함 |
| POST | `/audio/{book_id}/chapters/upload` | 파일 업로드(로컬 더미) | 프로덕션에서는 비활성 |

### 5.5 파일 API

| 메서드 | 경로 | 설명 | 요구사항 |
| --- | --- | --- | --- |
| POST | `/files/upload` | 일반 파일 업로드 | 쿼리 `user_id`, `book_id`, `file_type`; 멀티파트 |
| POST | `/files/upload/audio` | 오디오 업로드 & 챕터 자동 생성 | 파일명으로 챕터명 추출 |
| POST | `/files/retry-processing/{chapter_id}` | 로컬에서 메타데이터 재처리 | 로컬 환경 전용 |
| GET | `/files/list` | 파일 목록 조회 | `prefix`, `limit` 지원 |
| GET | `/files/info/{file_key}` | 파일 정보 조회 | URL 인코딩 필요 |
| GET | `/files/{file_key}` | 파일 다운로드 / 스트리밍 | Range 헤더 지원 |
| DELETE | `/files/{file_key}` | 파일 삭제 | 관리자 스코프 |
| GET | `/files/presigned-upload-url` | 프로덕션용 업로드 URL | ENV `production` 전용 |

### 5.6 로그 · WebSocket

| 메서드 | 경로 | 설명 | 비고 |
| --- | --- | --- | --- |
| POST | `/logs/backup` | 로그 세션 백업(JSON 저장) | 로컬 전용 |
| GET | `/logs/backups` | 백업 목록 조회 | 관리자 |
| DELETE | `/logs/backups/{filename}` | 백업 삭제 | 관리자 |
| POST | `/logs/cleanup` | 오래된 로그 정리 | 기본 30일 |
| GET | `/logs/stats` | WebSocket·백업 통계 | 관리자 |

#### WebSocket 채널

| 프로토콜 | 경로 | 설명 | 초기 행동 |
| --- | --- | --- | --- |
| `wss://` 또는 `ws://` | `/ws/logs` | 실시간 로그 스트림 | 접속 후 `subscribe`/`unsubscribe` 메시지 처리 |
| `wss://` 또는 `ws://` | `/ws/status/{chapter_id}` | 챕터 인코딩·상태 모니터링 | 서버가 즉시 상태 푸시 |

**메시지 규칙**
- 클라이언트 → 서버:
  ```json
  { "type": "subscribe", "chapter_id": "<uuid>" }
  { "type": "unsubscribe", "chapter_id": "<uuid>" }
  { "type": "get_history", "limit": 50 }
  { "type": "ping" }
  ```
- 서버 → 클라이언트: `type` 필드로 `connection`, `log`, `history`, `chapter_status`, `error`, `pong` 등을 전달.

## 6. 상세 요청/응답 예시

### 6.1 책 목록 조회

```
GET /api/v1/books?page=1&size=10
Authorization: Bearer <token>
Accept: application/json
```

**성공 응답**
```json
{
  "books": [
    {
      "book_id": "2f1c...",
      "user_id": "simple-user-admin",
      "title": "Demo Book",
      "author": "홍길동",
      "status": "draft",
      "total_chapters": 3,
      "total_duration": 5400,
      "created_at": "2024-03-01T08:10:45.123456",
      "updated_at": "2024-03-05T02:14:20.987654"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "has_next": false
}
```

### 6.2 오디오 스트리밍 URL 발급

```
GET /api/v1/audio/{bookId}/chapters/{chapterId}/stream
Authorization: Bearer <token>
```

**성공 응답**
```json
{
  "streaming_url": "/api/v1/files/uploads/user/book/abc123.m4a",
  "expires_at": "2024-05-01T23:59:59+00:00",
  "duration": 1320
}
```

> **Flutter 재생 팁**: `Uri.parse(streaming_url).isAbsolute` 검사 후 절대경로가 아니면 `https://voj-production.up.railway.app`를 prepend 하세요. `just_audio`는 Range 요청을 지원하므로 그대로 사용 가능합니다.

### 6.3 멀티파트 업로드(`/files/upload`)

```
POST /api/v1/files/upload?user_id=<sub>&book_id=<bookId>&file_type=upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
```

**성공 응답**
```json
{
  "success": true,
  "file_id": "4d0f...",
  "key": "uploads/<user>/<book>/<file_id>_chapter01.m4a",
  "size": 1048576,
  "content_type": "audio/x-m4a",
  "url": "http://localhost:8080/storage/uploads/...",
  "message": "File uploaded successfully"
}
```

> **검증 실패 (413)**: `{ "detail": "File size exceeds limit. Maximum allowed: 100.0MB" }`

### 6.4 WebSocket 로그 수신 예시

```json
// 서버 → 클라이언트 (type=log)
{
  "type": "log",
  "data": {
    "id": "f1a5...",
    "timestamp": "2024-04-30T10:02:15.432123+00:00",
    "level": "info",
    "category": "upload",
    "message": "Upload started: chapter01.m4a",
    "details": { "file_size": 5232234 },
    "chapter_id": "5b2c..."
  }
}
```

Flutter에서는 `web_socket_channel` 또는 `stomp_dart_client`로 구독하고, 메시지 `type`에 따라 접근성 알림(TTS/햅틱)을 트리거합니다.

## 7. Flutter 연동 체크리스트

- **의존성**
  - `dio`(HTTP), `web_socket_channel`(WS), `just_audio`(재생), `permission_handler`(마이크 업로드 시).
  - `json_serializable`로 DTO 생성: `Book`, `AudioChapter`, `StreamingUrlResponse`, `UploadResponse`.
- **HTTP 인터셉터**
  - 토큰 만료(401) 시 자동 로그아웃 및 재로그인 유도.
  - 요청 로깅 시 민감정보(토큰) 마스킹.
- **오프라인 캐시**
  - 책/챕터 목록은 `floor` 또는 `isar`에 저장하여 오프라인 접근 지원.
- **접근성 피드백**
  - 업로드 진행률, 연결 성공/실패, 스트림 재생 상태를 음성/햅틱으로 안내.
- **에러 처리**
  - `detail` 메시지를 사용자 친화적 문구로 변환.
  - 429/500 시 재시도 지연 및 사용자 선택 제공.
- **보안**
  - 토큰은 안전한 저장소(`flutter_secure_storage`)에 보관.
  - 로그 전송 시 PII 제거.
- **테스트**
  - `integration_test`로 로그인 → 스트림 재생 → 로그 수신까지 최소 1개 시나리오 자동화.
- **릴리스 체크**
  - 배포 전 API 변화 감시: Swagger 스키마와 이 문서를 비교, 변경 시 앱 업데이트 동시 배포.

## 8. 문제 해결 가이드

| 현상 | 원인 | 대응 |
| --- | --- | --- |
| 401 Unauthorized | 토큰 만료/미첨부 | 로그인 재시도, 인터셉터에서 자동 갱신 로직 확인 |
| 403 Forbidden | 스코프 부족 | 현재는 admin만 허용. 향후 역할 분리 시 백엔드 이슈 트래킹 |
| 404 Not Found | 잘못된 ID 또는 소유권 미일치 | 로그인 사용자와 리소스 소유자 동일 여부 확인 |
| 413 Payload Too Large | 파일 100MB 초과 | 업로드 전에 파일 크기 체크 or 분할 업로드 |
| 500 Internal Server Error | 스토리지/DB 문제 | `/health/detailed`로 의존성 상태 확인, 로그 스트림에서 에러 메시지 확인 |
| WebSocket 끊김 | 네트워크 불안정 | 자동 재연결(지수 백오프), `ping` 전송으로 keep-alive |

## 9. 변경 관리
- Swagger 문서(`openapi.json`)가 업데이트되면 이 문서도 동일 브랜치에서 갱신합니다.
- 앱 릴리스 전 체크리스트
  1. `poetry run pytest` (백엔드)
  2. `npm run lint` / `npm run build` (관리 콘솔)
  3. Flutter E2E 시나리오 (실시간 스트림)
- 프로덕션 문제 발생 시
  - `/logs/stats`에서 연결수·백업 현황 확인
  - 필요 시 `/logs/backup`으로 이슈 재현 로그 확보 후 SRE 공유

---

이 문서는 백엔드 스펙 변경 시마다 업데이트되어야 하며, Flutter 개발팀은 새 릴리스에 앞서 본 문서와 Swagger를 동시에 검토해야 합니다.
