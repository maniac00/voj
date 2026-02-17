import 'dart:async';
import 'package:just_audio/just_audio.dart';

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
  AudioPlayerService._internal();

  final AudioPlayer _player = AudioPlayer();
  final AudioService _audioService = AudioService();
  final AccessibilityFeedbackService _feedbackService = const AccessibilityFeedbackService();
  final AnalyticsService _analyticsService = AnalyticsService();

  Future<void> Function(AudioServiceException error)? _onUnauthorized;
  Future<void> Function(String message)? _onError;

  // 현재 재생 중인 정보
  Book? _currentBook;
  AudioChapter? _currentChapter;
  List<AudioChapter>? _playlist;
  int _currentIndex = 0;

  // 진행률 업데이트 타이머
  Timer? _progressTimer;
  
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
  Duration get position => _player.position;
  double get speed => _player.speed;

  String? _authToken;

  /// 인증 토큰 설정
  void setAuthToken(String token) {
    _authToken = token;
    _audioService.setAuthToken(token);
    _analyticsService.setAuthToken(token);
  }

  /// 인증 토큰 클리어
  void clearAuthToken() {
    _authToken = null;
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

  /// 오디오 파일 재생 시작
  Future<void> playChapter({
    required Book book,
    required AudioChapter chapter,
    List<AudioChapter>? playlist,
    int? startPosition,
  }) async {
    try {
      if (_currentChapter?.id == chapter.id) {
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

      final streaming = await _audioService.getStreamingUrl(
        bookId: book.id,
        chapterId: chapter.id,
      );
      await _player.setUrl(
        streaming.absoluteUrl,
        headers: _authToken != null
            ? {'Authorization': 'Bearer $_authToken'}
            : null,
      );

      if (startPosition != null && startPosition > 0) {
        await _player.seek(Duration(seconds: startPosition));
      } else {
        await _restorePlaybackPosition();
      }

      await _player.play();
      _startProgressTracking();
      _analyticsService.startPlaySession(bookId: book.id, chapterId: chapter.id);
      await _feedbackService.announce('${chapter.displayName} 재생을 시작합니다', withHaptic: true);
    } on AudioServiceException catch (error) {
      await _handleUnauthorizedError(error);
      await _feedbackService.error('오디오 스트리밍에 실패했습니다: ${error.message}');
      _onError?.call(error.message);
      throw AudioPlayerException('오디오 재생 중 오류가 발생했습니다: ${error.message}');
    } catch (error) {
      await _feedbackService.error('오디오 재생 중 알 수 없는 오류가 발생했습니다');
      _onError?.call(error.toString());
      throw AudioPlayerException('오디오 재생 중 오류가 발생했습니다: $error');
    }
  }

  /// 재생
  Future<void> play() async {
    await _player.play();
    _startProgressTracking();
  }

  /// 일시정지
  Future<void> pause() async {
    await _player.pause();
    await _saveCurrentProgress();
    await _analyticsService.endPlaySession();
    _stopProgressTracking();
  }

  /// 재생 재개
  Future<void> resume() async {
    await _player.play();
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
        position: _player.position.inSeconds,
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
        await _player.seek(Duration(seconds: position.position));
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
