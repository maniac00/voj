# Voice of Juan Mobile App 🎧📚

시각장애인을 위한 오디오북 스트리밍 앱

## 프로젝트 개요

Voice of Juan은 시각장애인을 위해 특별히 설계된 오디오북 플랫폼입니다. 접근성을 최우선으로 고려하여 개발되었으며, 직관적인 음성 인터페이스와 간편한 조작을 제공합니다.

## 주요 기능 ✨

### 🎵 오디오 스트리밍
- **실시간 스트리밍**: HTTP Range Request를 통한 효율적인 오디오 스트리밍
- **백그라운드 재생**: 앱을 벗어나도 계속되는 오디오 재생
- **재생 위치 동기화**: 서버와 실시간 진행률 동기화
- **자동 재개**: 마지막 재생 위치에서 자동 재개

### 🎛️ 재생 제어
- **미니 플레이어**: 전역에서 접근 가능한 미니 플레이어
- **전체 화면 플레이어**: 앨범 아트와 고급 제어 기능
- **재생 속도 조절**: 0.5x ~ 2.0x 가변 재생 속도
- **탐색 제어**: 15초 앞/뒤로 이동 기능

### 📖 도서 관리
- **카테고리별 분류**: 체계적인 도서 분류 시스템
- **검색 기능**: 제목, 저자로 도서 검색
- **북마크**: 중요한 위치 저장 및 메모 추가
- **재생 기록**: 개인별 재생 기록 관리

### ♿ 접근성
- **스크린 리더 지원**: VoiceOver/TalkBack 완전 호환
- **키보드 탐색**: 전체 키보드 제어 지원
- **고대비 모드**: 시각적 명료성 향상
- **의미론적 UI**: 명확한 음성 안내

## 기술 스택 🛠️

### Frontend (Flutter)
- **Flutter 3.8+**: 크로스 플랫폼 모바일 개발
- **Riverpod**: 상태 관리 및 의존성 주입
- **just_audio**: 고성능 오디오 재생
- **http/dio**: REST API 통신

### Backend Integration
- **Node.js/Express**: RESTful API 서버
- **PostgreSQL**: 데이터베이스
- **JWT**: 인증 및 권한 관리
- **Prisma**: ORM 및 데이터베이스 관리

## 설치 및 실행 🚀

### 사전 요구사항
- Flutter SDK 3.8.1 이상
- Dart SDK 3.0.0 이상
- Android Studio / Xcode (플랫폼별)
- Node.js 18+ (백엔드 실행용)

### 프로젝트 설정

1. **저장소 클론**
   ```bash
   git clone [repository-url]
   cd voiceofjuan/mobile/voice_of_juan
   ```

2. **의존성 설치**
   ```bash
   flutter pub get
   ```

3. **백엔드 서버 실행**
   ```bash
   cd ../../backend
   npm install
   npm run dev
   ```

4. **Flutter 앱 실행**
   ```bash
   flutter run
   ```

### 환경 설정

API 베이스 URL 설정 (`lib/data/services/api_service.dart`):
```dart
static const String baseUrl = 'http://localhost:3000/api';
```

## 프로젝트 구조 📁

```
lib/
├── core/                    # 핵심 유틸리티
│   ├── constants/          # 상수 정의
│   ├── theme/             # 앱 테마 설정
│   └── utils/             # 공통 유틸리티
├── data/                   # 데이터 레이어
│   ├── models/            # 데이터 모델
│   ├── repositories/      # 데이터 저장소
│   └── services/          # API 서비스
│       ├── api_service.dart       # 기본 API 통신
│       ├── book_service.dart      # 도서 관련 API
│       ├── audio_service.dart     # 오디오 스트리밍 API
│       └── audio_player_service.dart  # 오디오 플레이어 제어
├── domain/                 # 도메인 레이어
│   ├── entities/          # 엔티티
│   └── usecases/          # 유스케이스
├── presentation/           # 프레젠테이션 레이어
│   ├── providers/         # 상태 관리
│   │   ├── auth_provider.dart     # 인증 상태
│   │   ├── book_provider.dart     # 도서 상태
│   │   └── audio_player_provider.dart  # 오디오 플레이어 상태
│   ├── screens/           # 화면
│   │   ├── splash_screen.dart     # 스플래시
│   │   ├── home_screen.dart       # 홈
│   │   ├── login_screen.dart      # 로그인
│   │   ├── books_screen.dart      # 도서 목록
│   │   ├── book_detail_screen.dart # 도서 상세
│   │   └── audio_player_screen.dart # 오디오 플레이어
│   └── widgets/           # 위젯
│       ├── accessibility_button.dart  # 접근성 버튼
│       ├── book_card.dart            # 도서 카드
│       ├── audio_player_widget.dart  # 오디오 플레이어 위젯
│       └── app_scaffold.dart         # 앱 스캐폴드
└── main.dart               # 앱 진입점
```

## API 엔드포인트 🌐

### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/user/profile` - 프로필 조회

### 도서
- `GET /api/books` - 도서 목록 조회
- `GET /api/books/:id` - 도서 상세 조회
- `GET /api/categories` - 카테고리 목록

### 오디오 스트리밍
- `GET /api/v1/audio/{book_id}/chapters/{chapter_id}/stream` - 오디오 스트리밍 URL 발급
- `POST /api/v1/audio/{book_id}/chapters/{chapter_id}/progress` - 재생 진행률 업데이트
- `GET /api/v1/audio/{book_id}/chapters/{chapter_id}/position` - 현재 재생 위치
- `GET /api/v1/audio/{book_id}/history` - 재생 기록

### WebSocket
- `WS /ws/logs` - 서버 로그 구독 (subscribe/unsubscribe, get_history)
- `WS /ws/status/{chapter_id}` - 챕터 상태 구독 (processing/ready/failed)

### 북마크
- `GET /api/bookmarks` - 북마크 목록
- `POST /api/bookmarks` - 북마크 추가
- `DELETE /api/bookmarks/:id` - 북마크 삭제

## 오디오 플레이어 사용법 🎵

### 기본 재생
```dart
// 오디오 파일 재생 시작
AudioPlayerUtils.playAudio(
  context,
  ref,
  book: book,
  chapter: chapter,
  playlist: book.chapters,
);
```

### 플레이어 제어
```dart
final controller = ref.read(audioPlayerControllerProvider);

// 재생/일시정지
await controller.play();
await controller.pause();

// 위치 이동
await controller.seek(Duration(seconds: 120));

// 속도 조절
await controller.setSpeed(1.5);

// 트랙 이동
await controller.skipToNext();
await controller.skipToPrevious();
```

### 상태 관리
```dart
// 현재 재생 상태 감시
final playerState = ref.watch(playerStateProvider);
final position = ref.watch(positionProvider);
final duration = ref.watch(durationProvider);

// 현재 재생 중인 정보
final currentBook = ref.watch(currentBookProvider);
final currentChapter = ref.watch(currentChapterProvider);
```

## 접근성 가이드라인 ♿

### 스크린 리더 최적화
- 모든 UI 요소에 의미론적 라벨 제공
- 버튼과 입력 필드의 명확한 설명
- 탐색 순서의 논리적 구성

### 키보드 탐색
- Tab 키를 통한 순차적 탐색
- Enter/Space를 통한 활성화
- 화살표 키를 통한 세부 제어

### 시각적 접근성
- 고대비 모드 지원
- 큰 글씨 옵션
- 색상에 의존하지 않는 정보 전달

## 성능 최적화 ⚡

### 오디오 스트리밍
- HTTP Range Request를 통한 점진적 로딩
- 백그라운드에서의 효율적인 버퍼링
- 네트워크 상태에 따른 적응적 품질 조절

### 상태 관리
- Riverpod을 통한 효율적인 상태 관리
- 불필요한 리빌드 최소화
- 메모리 누수 방지

### 배터리 최적화
- 백그라운드 재생 시 최소한의 리소스 사용
- 화면 꺼짐 시 자동 최적화
- 네트워크 사용량 최적화

## 테스트 🧪

### 단위 테스트 실행
```bash
flutter test
```

### 통합 테스트 실행
```bash
flutter drive --target=test_driver/app.dart
```

### 정적 분석
```bash
flutter analyze
```

## 빌드 및 배포 📦

### Android APK 빌드
```bash
flutter build apk --release
```

### iOS IPA 빌드
```bash
flutter build ios --release
```

### 앱 번들 빌드 (Google Play)
```bash
flutter build appbundle --release
```

## 문제 해결 🔧

### 일반적인 문제

1. **오디오 재생 안됨**
   - 백엔드 서버 실행 상태 확인
   - 네트워크 연결 상태 확인
   - 오디오 파일 존재 여부 확인

2. **로그인 실패**
   - API 엔드포인트 URL 확인
   - 사용자 계정 승인 상태 확인

3. **앱 크래시**
   - Flutter와 Dart SDK 버전 확인
   - 의존성 버전 호환성 확인

### 디버그 로그 활성화
```dart
// main.dart에서 디버그 모드 활성화
void main() {
  if (kDebugMode) {
    debugPrint('Debug mode enabled');
  }
  runApp(MyApp());
}
```

## 기여 가이드 🤝

1. Fork 프로젝트
2. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

### 코딩 컨벤션
- Dart 공식 스타일 가이드 준수
- 접근성 가이드라인 준수
- 모든 공개 API에 문서화 주석 작성

## 라이선스 📄

이 프로젝트는 [MIT 라이선스](LICENSE) 하에 배포됩니다.

## 연락처 📞

프로젝트 관리자: Voice of Juan Team
이메일: contact@voiceofjuan.com

## 감사의 말 🙏

- Flutter 팀의 훌륭한 프레임워크
- just_audio 라이브러리 개발자들
- 시각장애인 커뮤니티의 피드백과 테스트 참여

---

*"모든 사람이 책의 즐거움을 누릴 수 있도록"* - Voice of Juan