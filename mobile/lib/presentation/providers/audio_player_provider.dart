import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../../data/services/audio_player_service.dart';
import '../../data/services/audio_service.dart';
import 'dart:async';
import '../../services/log_websocket_service.dart';
import '../../services/status_websocket_service.dart';
import '../../data/models/book_model.dart';
import 'auth_provider.dart';
// accessibilityFeedbackProvider는 auth_provider.dart에 정의됨

/// 오디오 플레이어 서비스 프로바이더
final audioPlayerServiceProvider = Provider<AudioPlayerService>((ref) {
  final service = AudioPlayerService();
  final authRepo = ref.watch(authRepositoryProvider);
  final accessibility = ref.watch(accessibilityFeedbackProvider);
  final prefs = ref.watch(sharedPreferencesProvider);
  final logService = LogWebSocketService();

  service.setSharedPreferences(prefs);

  service.registerUnauthorizedHandler((error) async {
    await service.saveProgressLocally();
    await authRepo.handleUnauthorized(
      message: '세션이 만료되었습니다. 다시 로그인해주세요.',
    );
  });

  service.registerErrorHandler((message) async {
    await accessibility.error('오디오 재생 오류: $message');
  });

  service.registerTokenRefresher(() async {
    final refreshed = await authRepo.refreshToken();
    if (refreshed) {
      final session = authRepo.currentSession;
      if (session != null) {
        service.setAuthToken(session.accessToken);
      }
    }
    return refreshed;
  });

  // 로그 WebSocket 연결 및 접근성 알림 연동
  logService.connect();
  final logSub = logService.stream.listen((event) async {
    final type = event['type'] as String?;
    if (type == 'log') {
      // 간단히 정보성 로그는 announce
      final data = event['data'] as Map<String, dynamic>?;
      final level = (data?['level'] ?? '').toString();
      final message = (data?['message'] ?? '').toString();
      if (level == 'error') {
        await accessibility.error('서버 로그 오류: $message');
      } else if (message.isNotEmpty) {
        await accessibility.announce('로그: $message');
      }
    }
  });

  ref.onDispose(() async {
    await logSub.cancel();
    await logService.dispose();
  });

  // 초기 세션으로 토큰 주입
  final initialSession = authRepo.currentSession;
  if (initialSession != null && initialSession.isValid) {
    service.setAuthToken(initialSession.accessToken);
  } else {
    service.clearAuthToken();
  }

  // 세션 변경을 구독하여 토큰 갱신
  ref.listen(authSessionProvider, (previous, next) {
    next.when(
      data: (session) {
        if (session != null && session.isValid) {
          service.setAuthToken(session.accessToken);
        } else {
          service.clearAuthToken();
        }
      },
      loading: () {},
      error: (_, __) => service.clearAuthToken(),
    );
  });

  return service;
});

/// 현재 재생 상태 프로바이더
final playerStateProvider = StreamProvider<PlayerState>((ref) {
  final audioPlayer = ref.watch(audioPlayerServiceProvider);
  return audioPlayer.playerStateStream;
});

/// 현재 재생 위치 프로바이더
final positionProvider = StreamProvider<Duration>((ref) {
  final audioPlayer = ref.watch(audioPlayerServiceProvider);
  return audioPlayer.positionStream;
});

/// 총 재생 시간 프로바이더
final durationProvider = StreamProvider<Duration?>((ref) {
  final audioPlayer = ref.watch(audioPlayerServiceProvider);
  return audioPlayer.durationStream;
});

/// 재생 속도 프로바이더
final speedProvider = StreamProvider<double>((ref) {
  final audioPlayer = ref.watch(audioPlayerServiceProvider);
  return audioPlayer.speedStream;
});

/// 현재 재생 중인 책 프로바이더
final currentBookProvider = StateProvider<Book?>((ref) => null);

/// 현재 재생 중인 오디오 챕터 프로바이더
final currentChapterProvider = StateProvider<AudioChapter?>((ref) => null);

/// 현재 플레이리스트 프로바이더
final playlistProvider = StateProvider<List<AudioChapter>?>((ref) => null);

/// 현재 재생 인덱스 프로바이더
final currentIndexProvider = StateProvider<int>((ref) => 0);

/// 미니 플레이어 표시 여부 프로바이더
final showMiniPlayerProvider = StateProvider<bool>((ref) => false);

/// 오디오 재생 에러 프로바이더 (AudioPlayerScreen에서 에러 표시용)
final audioPlayerErrorProvider = StateProvider<String?>((ref) => null);

/// 오디오 재생 로딩 상태 프로바이더
final audioPlayerLoadingProvider = StateProvider<bool>((ref) => false);

/// 현재 챕터 상태 텍스트 (WS 기반)
final currentChapterStatusProvider = StateProvider<String?>((ref) => null);

/// 오디오 플레이어 컨트롤러 프로바이더
final audioPlayerControllerProvider = Provider<AudioPlayerController>((ref) {
  final controller = AudioPlayerController(ref);

  // 스트림 상태 감시
  // 주의: resume()을 여기서 호출하면 안 됨 — setUrl 도중 ready 이벤트에 반응하여
  // 조기 play()가 발생하고, setUrl 완료 후 processingState가 idle로 리셋되는 문제 발생
  ref.listen(playerStateProvider, (prev, next) {
    next.whenData((state) {
      // playing 확인 시 로딩 플래그 해제
      final isInitiating = ref.read(audioPlayerLoadingProvider);
      if (isInitiating && state.playing) {
        ref.read(audioPlayerLoadingProvider.notifier).state = false;
      }

      // 챕터 재생 완료 시 자동으로 다음 챕터 재생
      if (state.processingState == ProcessingState.completed) {
        controller._autoPlayNext();
      }
    });
  });

  ref.onDispose(() {
    controller._statusSub?.cancel();
    controller._statusWs?.dispose();
  });
  return controller;
});

/// 오디오 플레이어 컨트롤러
class AudioPlayerController {
  final Ref _ref;

  AudioPlayerController(this._ref);

  AudioPlayerService get _service => _ref.read(audioPlayerServiceProvider);
  StreamSubscription? _statusSub;
  StatusWebSocketService? _statusWs;

  /// 오디오 파일 재생
  Future<void> playChapter({
    required Book book,
    required AudioChapter chapter,
    List<AudioChapter>? playlist,
    int? startPosition,
  }) async {
    try {
      // 에러 초기화, 로딩 시작
      _ref.read(audioPlayerErrorProvider.notifier).state = null;
      _ref.read(audioPlayerLoadingProvider.notifier).state = true;

      // 상태를 먼저 업데이트하여 UI가 즉시 반영되도록 함
      _ref.read(currentBookProvider.notifier).state = book;
      _ref.read(currentChapterProvider.notifier).state = chapter;
      _ref.read(playlistProvider.notifier).state = playlist ?? book.chapters;
      _ref.read(currentIndexProvider.notifier).state =
          (playlist ?? book.chapters).indexWhere((candidate) => candidate.id == chapter.id);
      _ref.read(showMiniPlayerProvider.notifier).state = true;
      _ref.read(currentChapterStatusProvider.notifier).state = '재생 준비 중';

      await _service.playChapter(
        book: book,
        chapter: chapter,
        playlist: playlist,
        startPosition: startPosition,
      );

      // 서비스에서 play() 후 playingStream.firstWhere(playing)까지 대기 완료됨
      // 리스너가 이미 loading flag를 해제했을 수 있지만, 안전장치로 여기서도 해제
      _ref.read(audioPlayerLoadingProvider.notifier).state = false;

      // 상태 WebSocket 구독 (fire-and-forget — 재생 시작을 블로킹하지 않음)
      _connectStatusWebSocket(chapter.id);

    } catch (e) {
      // Loading interrupted — 사용자가 빠르게 다른 트랙을 선택한 경우
      // 에러 상태를 설정하지 않고 조용히 반환
      if (e is AudioPlayerException && e.message == 'Loading interrupted') {
        return;
      }
      _ref.read(audioPlayerLoadingProvider.notifier).state = false;
      _ref.read(audioPlayerErrorProvider.notifier).state = e.toString();
      rethrow;
    }
  }

  /// 재생
  Future<void> play() async {
    await _service.play();
  }

  /// 일시정지
  Future<void> pause() async {
    _ref.read(audioPlayerLoadingProvider.notifier).state = false;
    await _service.pause();
  }

  /// 재생 재개
  Future<void> resume() async {
    await _service.resume();
  }

  /// 정지
  Future<void> stop() async {
    await _service.stop();
    _clearCurrentPlayback();
  }

  /// 특정 위치로 이동
  Future<void> seek(Duration position) async {
    await _service.seek(position);
  }

  /// 재생 속도 설정
  Future<void> setSpeed(double speed) async {
    await _service.setSpeed(speed);
  }

  /// 챕터 완료 시 자동으로 다음 챕터 재생
  Future<void> _autoPlayNext() async {
    if (_service.hasNext) {
      await skipToNext();
    }
  }

  /// 다음 트랙
  Future<void> skipToNext() async {
    if (!_service.hasNext) return;

    await _service.skipToNext();

    _ref.read(currentChapterProvider.notifier).state = _service.currentChapter;
    _ref.read(currentIndexProvider.notifier).state = _service.currentIndex;
  }

  /// 이전 트랙
  Future<void> skipToPrevious() async {
    if (!_service.hasPrevious) return;

    await _service.skipToPrevious();

    _ref.read(currentChapterProvider.notifier).state = _service.currentChapter;
    _ref.read(currentIndexProvider.notifier).state = _service.currentIndex;
  }

  /// 셔플 모드 토글
  Future<void> toggleShuffleMode() async {
    await _service.toggleShuffleMode();
  }

  /// 반복 모드 설정
  Future<void> setLoopMode(LoopMode loopMode) async {
    await _service.setLoopMode(loopMode);
  }

  /// 현재 재생 정보 초기화
  void _clearCurrentPlayback() {
    _service.clearCurrentPlayback();
    _ref.read(currentBookProvider.notifier).state = null;
    _ref.read(currentChapterProvider.notifier).state = null;
    _ref.read(playlistProvider.notifier).state = null;
    _ref.read(currentIndexProvider.notifier).state = 0;
    _ref.read(showMiniPlayerProvider.notifier).state = false;
    _ref.read(currentChapterStatusProvider.notifier).state = null;
    _ref.read(audioPlayerErrorProvider.notifier).state = null;
    _ref.read(audioPlayerLoadingProvider.notifier).state = false;
    _statusSub?.cancel();
    _statusSub = null;
    _statusWs?.dispose();
    _statusWs = null;
  }

  /// 상태 WebSocket을 비동기로 연결 (fire-and-forget)
  void _connectStatusWebSocket(String chapterId) async {
    await _statusSub?.cancel();
    await _statusWs?.dispose();
    _statusWs = StatusWebSocketService(chapterId);
    _statusWs!.connect().catchError((_) {});
    _statusSub = _statusWs!.stream.listen((event) async {
      final type = event['type'] as String?;
      if (type == 'chapter_status') {
        final status = (event['status'] ?? '').toString().toLowerCase();
        String? text;
        switch (status) {
          case 'processing':
            text = '인코딩 중';
            break;
          case 'ready':
            text = '재생 가능';
            break;
          case 'failed':
            text = '실패';
            break;
        }
        _ref.read(currentChapterStatusProvider.notifier).state = text;
      } else if (type == 'error') {
        final msg = (event['message'] ?? '상태 채널 오류').toString();
        _ref.read(currentChapterStatusProvider.notifier).state = '오류';
        final accessibility = _ref.read(accessibilityFeedbackProvider);
        await accessibility.error(msg);
      }
    });
  }

  /// 미니 플레이어 숨기기
  void hideMiniPlayer() {
    _ref.read(showMiniPlayerProvider.notifier).state = false;
  }

  /// 미니 플레이어 표시
  void showMiniPlayer() {
    _ref.read(showMiniPlayerProvider.notifier).state = true;
  }

  /// 재생 기록 조회
  Future<List<PlaybackHistory>> getPlaybackHistory(String bookId) async {
    return await _service.getPlaybackHistory(bookId);
  }

  /// 인증 토큰 설정
  void setAuthToken(String token) {
    _service.setAuthToken(token);
  }

  /// 인증 토큰 클리어
  void clearAuthToken() {
    _service.clearAuthToken();
  }
}

/// 현재 재생 상태를 나타내는 모델
class AudioPlayerState {
  final bool isPlaying;
  final bool isPaused;
  final bool isLoading;
  final Duration position;
  final Duration? duration;
  final double speed;
  final Book? currentBook;
  final AudioChapter? currentChapter;
  final List<AudioChapter>? playlist;
  final int currentIndex;
  final bool hasNext;
  final bool hasPrevious;
  final String? error;

  const AudioPlayerState({
    this.isPlaying = false,
    this.isPaused = false,
    this.isLoading = false,
    this.position = Duration.zero,
    this.duration,
    this.speed = 1.0,
    this.currentBook,
    this.currentChapter,
    this.playlist,
    this.currentIndex = 0,
    this.hasNext = false,
    this.hasPrevious = false,
    this.error,
  });

  AudioPlayerState copyWith({
    bool? isPlaying,
    bool? isPaused,
    bool? isLoading,
    Duration? position,
    Duration? duration,
    double? speed,
    Book? currentBook,
    AudioChapter? currentChapter,
    List<AudioChapter>? playlist,
    int? currentIndex,
    bool? hasNext,
    bool? hasPrevious,
    String? error,
  }) {
    return AudioPlayerState(
      isPlaying: isPlaying ?? this.isPlaying,
      isPaused: isPaused ?? this.isPaused,
      isLoading: isLoading ?? this.isLoading,
      position: position ?? this.position,
      duration: duration ?? this.duration,
      speed: speed ?? this.speed,
      currentBook: currentBook ?? this.currentBook,
      currentChapter: currentChapter ?? this.currentChapter,
      playlist: playlist ?? this.playlist,
      currentIndex: currentIndex ?? this.currentIndex,
      hasNext: hasNext ?? this.hasNext,
      hasPrevious: hasPrevious ?? this.hasPrevious,
      error: error ?? this.error,
    );
  }

  /// 재생 진행률 (0.0 - 1.0)
  double get progress {
    if (duration == null || duration!.inMilliseconds == 0) return 0.0;
    return position.inMilliseconds / duration!.inMilliseconds;
  }

  /// 남은 시간
  Duration get remainingTime {
    if (duration == null) return Duration.zero;
    return duration! - position;
  }

  /// 현재 위치 텍스트
  String get positionText {
    final minutes = position.inMinutes;
    final seconds = position.inSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  /// 총 시간 텍스트
  String get durationText {
    if (duration == null) return '--:--';
    final minutes = duration!.inMinutes;
    final seconds = duration!.inSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
}
