## Relevant Files

- `mobile/lib/core/constants/app_config.dart` - ENV 기반 API 베이스 URL과 공통 경로 생성 유틸리티.
- `mobile/lib/data/services/api_service.dart` - 인증 토큰 저장·요청 헤더 및 베이스 URL 구성을 스트리밍 API 사양에 맞게 조정.
- `mobile/lib/data/repositories/auth_repository.dart` - 로그인·로그아웃 흐름을 신규 토큰 응답 구조와 보안 저장소에 연계.
- `mobile/lib/data/services/book_service.dart` - 도서·챕터 API 경로 및 응답 스키마 변경 반영.
- `mobile/lib/data/services/audio_service.dart` - 스트리밍 URL 발급, 진행률 업데이트, 메타데이터 조회를 새 엔드포인트로 전환.
- `mobile/lib/data/services/audio_player_service.dart` - just_audio 재생 로직과 인증 오류 대응을 서버 URL 흐름에 맞게 보완.
- `mobile/lib/services/accessibility_feedback_service.dart` - 접근성 음성/햅틱 피드백을 제공하는 공통 유틸리티.
- `mobile/lib/data/models/book_model.dart` - 책·챕터 모델을 API 응답 필드와 일치하도록 재정의.
- `mobile/lib/data/models/user_model.dart` - 로그인 토큰 세션(`AuthSession`)과 `GET /auth/me` 응답 모델 정의.
- `mobile/lib/presentation/providers/auth_provider.dart` - 토큰 세션 스트림·보안 저장소 기반 상태 노출 및 재로그인 제어.
- `mobile/lib/presentation/providers/audio_player_provider.dart` - 플레이어 상태와 진행률 저장을 신규 서비스 메서드와 동기화.
- `mobile/lib/presentation/screens/login_screen.dart` - 로그인·오류 메시지·접근성 안내를 업데이트된 인증 흐름에 맞춤.
- `mobile/lib/presentation/screens/home_screen.dart` - 사용자 정보 표시를 스트리밍 프로필 데이터와 호환되게 조정.
- `mobile/lib/presentation/screens/books_screen.dart` - 서버 페이징·검색 파라미터·오프라인 캐시를 반영.
- `mobile/lib/presentation/screens/book_detail_screen.dart` - 챕터 리스트와 스트리밍 URL 요청·재생 진입점을 조정.
- `mobile/lib/presentation/screens/audio_player_screen.dart` - 스트리밍 재생 UI, 로그/상태 알림 연동.
- `mobile/lib/presentation/providers/book_provider.dart` - 세션 기반 토큰 주입과 도서·챕터 상태 관리를 갱신.
- `mobile/lib/data/repositories/book_repository.dart` - 서버 오류/권한 처리와 캐시 관리를 담당.
- `mobile/lib/services` (신규 WebSocket·캐시 유틸 예정) - 로그/상태 채널 클라이언트와 오프라인 저장 유틸 추가 지점.
- `mobile/test/` - 인증, 도서 로딩, 플레이어 흐름 테스트 케이스를 확장.
- `mobile/pubspec.yaml` - 모바일 앱 의존성(secure storage 등) 추가 및 버전 관리.

### Notes

- 단위 테스트는 서비스·리포지토리와 동일 디렉토리에 배치하고, 통합 시나리오는 `integration_test/`에 별도로 구성합니다.
- WebSocket 연결과 just_audio 스트리밍은 실제 백엔드 없이도 모의 서버로 검증 가능한 구조를 유지합니다.
- Flutter 빌드 시 `dart run build_runner build`가 필요하면 문서화하여 개발 흐름에 포함합니다.

## Tasks

- [ ] 1.0 API 클라이언트와 인증을 스트리밍 스펙에 맞게 재구성
  - [x] 1.1 `ApiService` 기본 URL을 `ENV` 기반으로 분리하고 `/api/v1` 접두사 및 공통 헤더를 통일한다.
  - [x] 1.2 로그인·토큰 응답(`access_token`, `expires_in`, `scope`)을 `AuthRepository`·`AuthProvider`에서 처리하고 보안 저장소 연동을 점검한다.
  - [x] 1.3 `GET /auth/me` 호출로 사용자 정보와 스코프를 로드하며 로컬 환경 우회 규칙을 반영한다.
  - [x] 1.4 401/403 응답 시 토큰 삭제·재로그인 유도 루틴과 접근성 알림(음성/진동)을 추가한다.

- [ ] 2.0 책·챕터 데이터 흐름과 화면을 원격 스트리밍 기반으로 조정
  - [x] 2.1 `BookService`를 `/books`, `/audio/{book_id}/chapters` 경로 구조에 맞춰 수정하고 페이지네이션·필터 파라미터를 정비한다. (카테고리 엔드포인트 미제공에 따라 빈 목록 처리)
  - [x] 2.2 `Book`·`AudioChapter`(신규) 모델을 API 응답(`books`, `total`, `has_next`, `status`)과 일치하도록 재정의한다.
  - [x] 2.3 `BooksScreen`과 `BookProvider`에서 서버 페이징, 검색을 지원하고 로딩/에러 상태 접근성 피드백을 구현한다. (카테고리 필터는 API 부재로 비활성화)
  - [ ] 2.4 `BookDetailScreen`에 챕터 목록·상태 표시·오프라인 캐시 갱신 로직을 적용한다.

- [ ] 3.0 오디오 플레이어를 서버 스트리밍 URL 중심으로 재작동
  - [ ] 3.1 `AudioService`에 `GET /audio/{book_id}/chapters/{chapter_id}/stream`·진행률 업데이트 API를 통합한다.
  - [ ] 3.2 `AudioPlayerService`에서 챕터 ID·스트리밍 URL을 인자로 받아 Range 요청 지원 설정과 오류 처리(413/404 등)를 추가한다.
  - [ ] 3.3 플레이리스트 이동, 셔플/반복, 진행률 저장 로직을 신규 API 계약에 맞춰 조정하고 실패 시 사용자 안내를 보강한다.
  - [ ] 3.4 재생 UI(`AudioPlayerScreen`, 미니 플레이어)에서 실시간 상태, 남은 시간, 접근성 안내를 업데이트한다.

- [ ] 4.0 실시간 로그·상태 WebSocket 연동 및 접근성 피드백 구현
  - [ ] 4.1 `/ws/logs` 채널 클라이언트 유틸을 작성해 `subscribe`·`get_history` 메시지를 처리하고 로그 목록을 상태로 저장한다.
  - [ ] 4.2 `/ws/status/{chapter_id}` 채널로 챕터 인코딩 상태를 구독하며 재생 준비/실패 알림을 UI와 TTS/햅틱으로 연결한다.
  - [ ] 4.3 WebSocket 재연결(지수 백오프)과 `ping`/`pong` 처리, 네트워크 오류 대응을 구현한다.
  - [ ] 4.4 접근성 설정 메뉴나 글로벌 피드백 모듈에서 로그·상태 메시지를 사용자 친화적 문구로 변환한다.

- [ ] 5.0 접근성·캐싱·테스트 전략을 스트리밍 시나리오로 보강
  - [ ] 5.1 `isar` 또는 `floor`를 사용해 책·챕터·로그 데이터를 오프라인 캐시하고 싱크 전략을 문서화한다.
  - [ ] 5.2 접근성(음성 안내·햅틱) 설정과 HTTP/WS 오류 메시지를 한글 내레이션/진동 패턴으로 통일한다.
  - [ ] 5.3 서비스·프로바이더 단위 테스트와 스트리밍 재생 통합 테스트(로그인→재생→로그 수신)를 작성한다.
  - [ ] 5.4 개발 환경 설정(`README.md`나 전용 문서)에 스트리밍 API, WebSocket, 캐시 초기화 절차를 추가한다.
