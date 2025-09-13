## Relevant Files

- `frontend/src/app/(auth)/login/page.tsx` - 하드코딩 로그인 폼으로 교체 (현재 Cognito 기반)
- `frontend/src/app/(auth)/login/page.test.tsx` - 하드코딩 로그인 테스트
- `frontend/src/lib/auth/simple-auth.ts` - 간단한 세션 기반 인증 유틸리티 (신규)
- `frontend/src/lib/auth/simple-auth.test.ts` - 간단한 인증 유틸리티 테스트
- `backend/app/core/auth/simple.py` - 하드코딩 인증 디펜던시 (신규)
- `backend/app/core/auth/simple.test.py` - 하드코딩 인증 테스트
- `frontend/src/app/(admin)/books/[bookId]/audios/page.tsx` - 파일 선택 버튼으로 수정 (현재 드래그앤드롭)
- `frontend/src/app/(admin)/books/[bookId]/audios/page.test.tsx` - 오디오 업로드 UI 테스트
- `frontend/src/components/audio/upload-form.tsx` - 파일 선택 업로드 컴포넌트 (신규)
- `frontend/src/components/audio/upload-form.test.tsx` - 업로드 폼 컴포넌트 테스트
- `frontend/src/components/audio/status-logger.tsx` - 실시간 로그 표시 컴포넌트 (신규)
- `frontend/src/components/audio/status-logger.test.tsx` - 로그 표시 컴포넌트 테스트
- `frontend/src/components/audio/audio-player.tsx` - 어드민 테스트용 오디오 플레이어 (신규)
- `frontend/src/components/audio/audio-player.test.tsx` - 오디오 플레이어 테스트
- `backend/app/api/v1/endpoints/audio.py` - 완전한 오디오 업로드/인코딩 구현
- `backend/app/api/v1/endpoints/audio.test.py` - 오디오 엔드포인트 테스트
- `backend/app/services/encoding/ffmpeg.py` - FFmpeg 인코딩 서비스 (신규)
- `backend/app/services/encoding/ffmpeg.test.py` - FFmpeg 서비스 테스트
- `backend/app/services/encoding/status.py` - 인코딩 상태 관리 서비스 (신규)
- `backend/app/services/encoding/status.test.py` - 상태 관리 서비스 테스트
- `backend/app/api/v1/endpoints/logs.py` - 실시간 로그 스트리밍 엔드포인트 (신규)
- `backend/app/api/v1/endpoints/logs.test.py` - 로그 엔드포인트 테스트
- `backend/app/services/websocket/manager.py` - WebSocket 연결 관리 (신규)
- `backend/app/services/websocket/manager.test.py` - WebSocket 관리자 테스트
- `frontend/src/hooks/use-encoding-logs.ts` - 실시간 로그 수신 훅 (신규)
- `frontend/src/hooks/use-encoding-logs.test.ts` - 로그 훅 테스트
- `frontend/src/app/(admin)/dashboard/page.tsx` - 대시보드 페이지 (신규)
- `frontend/src/app/(admin)/dashboard/page.test.tsx` - 대시보드 테스트
- `backend/app/core/settings/base.py` - 하드코딩 인증 설정 추가
- `backend/app/main.py` - WebSocket 지원 추가
- `docker-compose.yml` - Redis 추가 (WebSocket 세션 관리용)

### Notes

- 현재 Cognito 기반 인증을 하드코딩 인증으로 교체
- 드래그앤드롭을 파일 선택 버튼으로 변경
- FFmpeg 인코딩 파이프라인 완전 구현
- WebSocket을 통한 실시간 로그 스트리밍 구현
- 모든 새로운 컴포넌트와 서비스에 대한 테스트 작성
- 환경별 설정 지원 (로컬/AWS)

## Tasks

- [x] 1.0 하드코딩 인증 시스템 구현 (FR-1, FR-2, FR-3)
  - [x] 1.1 백엔드 하드코딩 인증 디펜던시 구현 (admin/admin123)
  - [x] 1.2 프론트엔드 간단한 로그인 폼 구현 (ID/Password 입력)
  - [x] 1.3 세션 기반 인증 상태 관리 구현
  - [x] 1.4 미인증 사용자 리디렉션 로직 구현
  - [x] 1.5 기존 Cognito 의존성 제거 및 정리
  - [x] 1.6 하드코딩 인증 시스템 테스트 작성
- [x] 2.0 책 관리 UI 완성 및 개선 (FR-4, FR-5, FR-6, FR-7)
  - [x] 2.1 책 생성 폼 UI 개선 및 유효성 검증
  - [x] 2.2 책 목록 테이블 UI 개선 및 정렬/필터링
  - [x] 2.3 책 상세/편집 페이지 UI 완성
  - [x] 2.4 책 삭제 확인 다이얼로그 및 안전 장치
  - [x] 2.5 에러 처리 및 로딩 상태 개선
  - [x] 2.6 접근성 강화 (키보드 내비게이션, ARIA)
- [x] 3.0 파일 선택 기반 오디오 업로드 구현 (FR-8, FR-9)
  - [x] 3.1 파일 선택 업로드 컴포넌트 구현 (드래그앤드롭 → 파일 버튼)
  - [x] 3.2 오디오 업로드 API 완전 구현 (백엔드)
  - [x] 3.3 업로드 진행률 및 상태 표시 UI
  - [x] 3.4 오디오 파일 유효성 검증 강화
  - [x] 3.5 업로드된 오디오 목록 및 관리 UI
  - [x] 3.6 오디오 업로드 에러 처리 및 재시도
- [ ] 4.0 FFmpeg 인코딩 파이프라인 완전 구현 (FR-10, FR-11)
- [ ] 5.0 실시간 상태 모니터링 및 로그 시스템 (FR-12, FR-13, FR-14, FR-15)
- [ ] 6.0 어드민 페이지 오디오 재생 기능 (FR-16, FR-17, FR-18)
- [ ] 7.0 환경별 설정 자동화 (FR-19, FR-20, FR-21)
- [ ] 8.0 대시보드 및 전체 워크플로우 통합
- [ ] 9.0 테스트 및 품질 보증
- [ ] 10.0 성능 최적화 및 에러 처리
