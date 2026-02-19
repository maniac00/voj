import 'dart:async';
import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';

import '../../core/utils/logger.dart';
import '../../services/accessibility_feedback_service.dart';
import '../models/book_model.dart';
import 'analytics_service.dart';
import 'audio_service.dart';

const _log = AppLogger('AudioPlayer');

/// 오디오 플레이어 서비스
/// just_audio를 사용하여 오디오 스트리밍 및 재생 제어를 제공
class AudioPlayerService {
  static final AudioPlayerService _instance = AudioPlayerService._internal();
  factory AudioPlayerService() => _instance;
  AudioPlayerService._internal() {
    _initErrorRecovery();
  }

  final AudioPlayer _player = AudioPlayer(
    audioLoadConfiguration: AudioLoadConfiguration(
      androidLoadControl: AndroidLoadControl(
        minBufferDuration: const Duration(seconds: 120),
        maxBufferDuration: const Duration(minutes: 10),
        bufferForPlaybackDuration: const Duration(seconds: 5),
        bufferForPlaybackAfterRebufferDuration: const Duration(seconds: 30),
      ),
    ),
  );
  final AudioService _audioService = AudioService();
  final AccessibilityFeedbackService _feedbackService = const AccessibilityFeedbackService();
  final AnalyticsService _analyticsService = AnalyticsService();

  Future<void> Function(AudioServiceException error)? _onUnauthorized;
  Future<void> Function(String message)? _onError;
  Future<bool> Function()? _tokenRefresher;

  // 현재 재생 중인 정보
  Book? _currentBook;
  AudioChapter? _currentChapter;
  List<AudioChapter>? _playlist;
  int _currentIndex = 0;

  // 진행률 업데이트 타이머
  Timer? _progressTimer;

  // 로컬 position 추적 — player.position이 stale할 수 있으므로 별도 관리
  Duration _lastKnownPosition = Duration.zero;
  StreamSubscription<Duration>? _positionSub;

  // 에러 자동 복구
  StreamSubscription<Object>? _errorSub;
  StreamSubscription<PlayerState>? _playerStateSub;
  Timer? _bufferingStallTimer;
  int _retryCount = 0;
  static const int _maxRetries = 3;
  bool _isRecovering = false;
  bool _isChangingSource = false; // 의도적 소스 변경 중 에러 복구 억제
  String? _lastStreamingUrl;

  // 스트림
  Stream<PlayerState> get playerStateStream => _player.playerStateStream;
  Stream<Duration?> get durationStream => _player.durationStream;
  Stream<Duration> get positionStream => _player.positionStream;
  Stream<double> get speedStream => _player.speedStream;
  Stream<bool> get shuffleModeEnabledStream => _player.shuffleModeEnabledStream;
  Stream<LoopMode> get loopModeStream => _player.loopModeStream;

  // Getters
  Book? get currentBook => _currentBook;
  AudioChapter? get currentChapter => _currentChapter;
  List<AudioChapter>? get playlist => _playlist;
  int get currentIndex => _currentIndex;
  bool get hasNext => _playlist != null && _currentIndex < _playlist!.length - 1;
  bool get hasPrevious => _playlist != null && _currentIndex > 0;
  bool get isPlaying => _player.playing;
  bool get isPaused => _player.processingState == ProcessingState.ready && !_player.playing;
  Duration? get duration => _player.duration;
  Duration get position => _lastKnownPosition;
  double get speed => _player.speed;

  String? _authToken;
  String? _headerToken; // setAudioSource() 시 사용한 토큰 기록

  /// 에러 복구 및 position 추적 초기화
  void _initErrorRecovery() {
    // position 추적: 1초마다 기록
    _positionSub = _player.positionStream.listen((pos) {
      if (pos > Duration.zero) {
        _lastKnownPosition = pos;
      }
    });

    // 에러 스트림 리스닝
    _errorSub = _player.playerStateStream
        .where((state) => state.processingState == ProcessingState.idle)
        .listen((_) {
      // idle 상태로 돌아갔으면 에러 발생일 수 있음
      // _isChangingSource가 true면 의도적 소스 변경(챕터 전환, resume 등)이므로 무시
      if (_currentChapter != null && !_isRecovering && !_isChangingSource) {
        _log.warning('Player went idle unexpectedly, attempting recovery');
        _attemptRecovery();
      }
    });

    // buffering stall 감지
    _playerStateSub = _player.playerStateStream.listen((state) {
      if (state.processingState == ProcessingState.buffering) {
        _bufferingStallTimer?.cancel();
        _bufferingStallTimer = Timer(const Duration(seconds: 30), () {
          if (_player.processingState == ProcessingState.buffering &&
              !_isRecovering &&
              !_isChangingSource) {
            _log.warning('Buffering stall detected (30s), attempting recovery');
            _attemptRecovery();
          }
        });
      } else {
        _bufferingStallTimer?.cancel();
        _bufferingStallTimer = null;
        if (state.processingState == ProcessingState.ready) {
          _retryCount = 0;
        }
      }
    });
  }

  /// 자동 재연결 시도
  Future<void> _attemptRecovery() async {
    if (_isRecovering ||
        _currentBook == null ||
        _currentChapter == null ||
        _lastStreamingUrl == null) {
      return;
    }

    if (_retryCount >= _maxRetries) {
      _log.severe('Max retries exceeded, giving up recovery');
      _retryCount = 0;
      _onError?.call('네트워크 연결이 불안정합니다. 다시 시도해 주세요.');
      return;
    }

    _isRecovering = true;
    _retryCount++;
    final posToRestore = _lastKnownPosition;
    _log.info('Recovery attempt $_retryCount/$_maxRetries at position ${posToRestore.inSeconds}s');

    try {
      await Future.delayed(const Duration(seconds: 3));

      // 토큰 갱신 시도
      if (_tokenRefresher != null) {
        await _tokenRefresher!();
      }

      final streaming = await _audioService.getStreamingUrl(
        bookId: _currentBook!.id,
        chapterId: _currentChapter!.id,
      );
      _headerToken = _authToken;
      _lastStreamingUrl = streaming.absoluteUrl;

      _isChangingSource = true;
      await _setAudioSourceWithTag(streaming.absoluteUrl);
      _isChangingSource = false;
      await _player.seek(posToRestore);
      unawaited(_player.play());
      _startProgressTracking();
      _log.info('Recovery successful');
    } catch (e) {
      _isChangingSource = false;
      _log.warning('Recovery attempt $_retryCount failed', error: e);
      // 다음 재시도는 에러 스트림이나 stall 타이머가 트리거
    } finally {
      _isRecovering = false;
    }
  }

  /// AudioSource.uri + MediaItem 태그로 오디오 소스 설정
  Future<void> _setAudioSourceWithTag(String url) async {
    final chapter = _currentChapter;
    final book = _currentBook;

    await _player.setAudioSource(
      AudioSource.uri(
        Uri.parse(url),
        headers: _headerToken != null
            ? {'Authorization': 'Bearer $_headerToken'}
            : null,
        tag: MediaItem(
          id: chapter?.id ?? '',
          title: chapter?.displayName ?? '오디오',
          artist: book?.author ?? '',
          album: book?.title ?? '',
          duration: chapter?.duration != null
              ? Duration(seconds: chapter!.duration!)
              : null,
        ),
      ),
    );
  }

  /// 인증 토큰 설정
  void setAuthToken(String token) {
    _authToken = token;
    _audioService.setAuthToken(token);
    _analyticsService.setAuthToken(token);
  }

  /// 인증 토큰 클리어
  void clearAuthToken() {
    _authToken = null;
    _headerToken = null;
    _audioService.clearAuthToken();
    _analyticsService.clearAuthToken();
  }

  void registerUnauthorizedHandler(
    Future<void> Function(AudioServiceException error) handler,
  ) {
    _onUnauthorized = handler;
  }

  void registerErrorHandler(Future<void> Function(String message) handler) {
    _onError = handler;
  }

  void registerTokenRefresher(Future<bool> Function() refresher) {
    _tokenRefresher = refresher;
  }

  /// 오디오 파일 재생 시작
  Future<void> playChapter({
    required Book book,
    required AudioChapter chapter,
    List<AudioChapter>? playlist,
    int? startPosition,
  }) async {
    _isChangingSource = true;
    try {
      if (_currentChapter?.id == chapter.id) {
        _isChangingSource = false;
        if (isPlaying) {
          await pause();
        } else {
          await resume();
        }
        return;
      }

      _currentBook = book;
      _playlist = playlist ?? book.chapters;
      _currentChapter = chapter;
      _currentIndex = _playlist!.indexWhere((candidate) => candidate.id == chapter.id);
      _retryCount = 0;
      _lastKnownPosition = Duration.zero;

      // TalkBack 접근성 알림을 오디오 로딩 전에 실행 — play() 이후 호출 시
      // TalkBack TTS가 Android 오디오 포커스를 빼앗아 processingState가 idle로 리셋됨
      await _feedbackService.announce('${chapter.displayName} 재생을 시작합니다', withHaptic: true);

      final streaming = await _audioService.getStreamingUrl(
        bookId: book.id,
        chapterId: chapter.id,
      );
      _headerToken = _authToken;
      _lastStreamingUrl = streaming.absoluteUrl;
      await _setAudioSourceWithTag(streaming.absoluteUrl);
      _isChangingSource = false;

      if (startPosition != null && startPosition > 0) {
        await _player.seek(Duration(seconds: startPosition));
        _lastKnownPosition = Duration(seconds: startPosition);
      } else {
        await _restorePlaybackPosition();
      }
      // play()를 await하면 오디오가 끝날 때까지 블로킹되므로 unawaited 처리하고,
      // 대신 playingStream으로 "재생 시작"만 확인한 뒤 반환
      unawaited(_player.play());
      await _player.playingStream
          .firstWhere((playing) => playing)
          .timeout(const Duration(seconds: 5), onTimeout: () => true);
      _startProgressTracking();
      _analyticsService.startPlaySession(bookId: book.id, chapterId: chapter.id);
    } on AudioServiceException catch (error) {
      _isChangingSource = false;
      _currentBook = null;
      _currentChapter = null;
      _playlist = null;
      _currentIndex = 0;
      await _handleUnauthorizedError(error);
      await _feedbackService.error('오디오 스트리밍에 실패했습니다: ${error.message}');
      _onError?.call(error.message);
      throw AudioPlayerException('오디오 재생 중 오류가 발생했습니다: ${error.message}');
    } catch (error) {
      _isChangingSource = false;
      _currentBook = null;
      _currentChapter = null;
      _playlist = null;
      _currentIndex = 0;
      await _feedbackService.error('오디오 재생 중 알 수 없는 오류가 발생했습니다');
      _onError?.call(error.toString());
      throw AudioPlayerException('오디오 재생 중 오류가 발생했습니다: $error');
    }
  }

  /// 재생
  Future<void> play() async {
    _player.play();
    _startProgressTracking();
  }

  /// 일시정지
  Future<void> pause() async {
    _lastKnownPosition = _player.position;
    await _player.pause();
    await _saveCurrentProgress();
    await _analyticsService.endPlaySession();
    _stopProgressTracking();
  }

  /// 재생 재개
  Future<void> resume() async {
    // 백그라운드에서 Firebase 토큰이 자동 갱신되지 않을 수 있으므로
    // resume 시 강제로 토큰 갱신을 시도한다.
    if (_tokenRefresher != null) {
      final oldToken = _authToken;
      await _tokenRefresher!();
      if (_authToken != oldToken) {
        _log.info('Token refreshed on resume');
      }
    }

    // 토큰이 갱신된 경우 — 만료된 헤더로 요청하면 401 에러 발생
    if (_authToken != _headerToken &&
        _currentBook != null &&
        _currentChapter != null) {
      _log.info('Token changed since last setAudioSource, refreshing audio source');
      _isChangingSource = true;
      final pos = _lastKnownPosition;
      final streaming = await _audioService.getStreamingUrl(
        bookId: _currentBook!.id,
        chapterId: _currentChapter!.id,
      );
      _headerToken = _authToken;
      _lastStreamingUrl = streaming.absoluteUrl;
      await _setAudioSourceWithTag(streaming.absoluteUrl);
      _isChangingSource = false;
      await _player.seek(pos);
    }
    _player.play();
    _startProgressTracking();
  }

  /// 정지
  Future<void> stop() async {
    await _player.stop();
    await _saveCurrentProgress();
    await _analyticsService.endPlaySession();
    _stopProgressTracking();
  }

  /// 특정 위치로 이동
  Future<void> seek(Duration position) async {
    await _player.seek(position);
    _lastKnownPosition = position;
    await _saveCurrentProgress();
  }

  /// 재생 속도 설정
  Future<void> setSpeed(double speed) async {
    await _player.setSpeed(speed);
  }

  /// 다음 트랙
  Future<void> skipToNext() async {
    if (!hasNext || _playlist == null || _currentBook == null) return;

    final nextChapter = _playlist![_currentIndex + 1];
    await playChapter(
      book: _currentBook!,
      chapter: nextChapter,
      playlist: _playlist,
    );
  }

  /// 이전 트랙
  Future<void> skipToPrevious() async {
    if (!hasPrevious || _playlist == null || _currentBook == null) return;

    final previousChapter = _playlist![_currentIndex - 1];
    await playChapter(
      book: _currentBook!,
      chapter: previousChapter,
      playlist: _playlist,
    );
  }

  /// 셔플 모드 토글
  Future<void> toggleShuffleMode() async {
    await _player.setShuffleModeEnabled(!_player.shuffleModeEnabled);
  }

  /// 반복 모드 설정
  Future<void> setLoopMode(LoopMode loopMode) async {
    await _player.setLoopMode(loopMode);
  }

  /// 현재 재생 위치 저장
  Future<void> _saveCurrentProgress() async {
    if (_currentChapter == null || _player.duration == null) return;

    try {
      await _audioService.updatePlaybackProgress(
        bookId: _currentBook!.id,
        chapterId: _currentChapter!.id,
        position: _lastKnownPosition.inSeconds,
        duration: _player.duration!.inSeconds,
      );
    } catch (e) {
      // 진행률 저장 실패는 재생에 영향을 주지 않음
      await _handleUnauthorizedError(e);
      _log.warning('Progress save failed', error: e);
    }
  }

  /// 이전 재생 위치 복원
  Future<void> _restorePlaybackPosition() async {
    if (_currentBook == null || _currentChapter == null) return;

    try {
      final position = await _audioService.getPlaybackPosition(
        bookId: _currentBook!.id,
        chapterId: _currentChapter!.id,
      );

      if (position != null && position.position > 0) {
        final dur = Duration(seconds: position.position);
        await _player.seek(dur);
        _lastKnownPosition = dur;
      }
    } catch (e) {
      await _handleUnauthorizedError(e);
      // 위치 복원 실패는 재생에 영향을 주지 않음
      _log.warning('Position restore failed', error: e);
    }
  }

  /// 진행률 추적 시작
  void _startProgressTracking() {
    _stopProgressTracking();

    _progressTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
      if (_player.playing) {
        _saveCurrentProgress();
      }
    });
  }

  /// 진행률 추적 중지
  void _stopProgressTracking() {
    _progressTimer?.cancel();
    _progressTimer = null;
  }

  /// 현재 재생 정보 초기화
  void clearCurrentPlayback() {
    _currentBook = null;
    _currentChapter = null;
    _playlist = null;
    _currentIndex = 0;
    _lastKnownPosition = Duration.zero;
    _lastStreamingUrl = null;
    _retryCount = 0;
    _isChangingSource = false;
    _stopProgressTracking();
  }

  /// 재생 기록 조회
  Future<List<PlaybackHistory>> getPlaybackHistory(String bookId) async {
    try {
      return await _audioService.getPlaybackHistory(bookId: bookId);
    } catch (e) {
      await _handleUnauthorizedError(e);
      rethrow;
    }
  }

  /// 리소스 정리
  Future<void> dispose() async {
    await _saveCurrentProgress();
    await _analyticsService.endPlaySession();
    _stopProgressTracking();
    _bufferingStallTimer?.cancel();
    _positionSub?.cancel();
    _errorSub?.cancel();
    _playerStateSub?.cancel();
    await _player.dispose();
    _audioService.dispose();
    _analyticsService.dispose();
  }

  Future<void> _handleUnauthorizedError(dynamic error) async {
    if (error is AudioServiceException &&
        (error.isUnauthorized || error.isForbidden) &&
        _onUnauthorized != null) {
      await _onUnauthorized!(error);
    }
  }
}

/// 오디오 플레이어 예외
class AudioPlayerException implements Exception {
  final String message;

  const AudioPlayerException(this.message);

  @override
  String toString() => 'AudioPlayerException: $message';
}
