import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/constants/app_config.dart';
import '../../core/utils/logger.dart';

const _log = AppLogger('Analytics');

/// 분석/통계 수집 서비스
/// 기기 등록, heartbeat, 재생 세션 기록
class AnalyticsService {
  static final AnalyticsService _instance = AnalyticsService._internal();
  factory AnalyticsService() => _instance;
  AnalyticsService._internal();

  final http.Client _client = http.Client();
  String? _authToken;
  String? _deviceId;

  // 현재 재생 세션 추적
  DateTime? _currentSessionStart;
  String? _currentSessionBookId;
  String? _currentSessionChapterId;

  void setAuthToken(String token) {
    _authToken = token;
  }

  void clearAuthToken() {
    _authToken = null;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  /// 고유 기기 ID를 가져오거나 새로 생성
  Future<String> _getDeviceId() async {
    if (_deviceId != null) return _deviceId!;

    final prefs = await SharedPreferences.getInstance();
    _deviceId = prefs.getString('voj_device_id');
    if (_deviceId == null) {
      _deviceId = _generateUuid();
      await prefs.setString('voj_device_id', _deviceId!);
    }
    return _deviceId!;
  }

  /// 간단한 UUID v4 생성 (uuid 패키지 없이)
  String _generateUuid() {
    final random = DateTime.now().microsecondsSinceEpoch;
    return '${random.toRadixString(16)}-${DateTime.now().millisecondsSinceEpoch.toRadixString(16)}-${random.hashCode.abs().toRadixString(16)}';
  }

  /// 기기 등록 (앱 최초 실행 시)
  Future<void> registerDevice() async {
    try {
      final deviceId = await _getDeviceId();

      String? osVersion;
      String? deviceModel;
      try {
        osVersion = '${Platform.operatingSystem} ${Platform.operatingSystemVersion}';
        deviceModel = Platform.localHostname;
      } catch (_) {}

      final uri = AppConfig.apiUri('/analytics/device-register');
      final response = await _client.post(
        uri,
        headers: _headers,
        body: json.encode({
          'device_id': deviceId,
          'platform': Platform.isAndroid ? 'android' : (Platform.isIOS ? 'ios' : 'other'),
          'os_version': osVersion,
          'app_version': '1.0.0',
          'device_model': deviceModel,
        }),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        _log.info('Device registered successfully');
      } else {
        _log.warning('Device registration failed: ${response.statusCode}');
      }
    } catch (e) {
      _log.warning('Device registration error', error: e);
    }
  }

  /// Heartbeat 전송 (앱 포그라운드 복귀 시)
  Future<void> sendHeartbeat() async {
    try {
      final deviceId = await _getDeviceId();
      final uri = AppConfig.apiUri('/analytics/heartbeat');
      await _client.post(
        uri,
        headers: _headers,
        body: json.encode({
          'device_id': deviceId,
          'app_version': '1.0.0',
        }),
      );
    } catch (e) {
      _log.warning('Heartbeat error', error: e);
    }
  }

  /// 재생 세션 시작
  void startPlaySession({
    required String bookId,
    required String chapterId,
  }) {
    // 기존 세션이 있으면 먼저 종료
    if (_currentSessionStart != null) {
      endPlaySession();
    }
    _currentSessionStart = DateTime.now().toUtc();
    _currentSessionBookId = bookId;
    _currentSessionChapterId = chapterId;
  }

  /// 재생 세션 종료 및 서버 전송
  Future<void> endPlaySession({bool completed = false}) async {
    if (_currentSessionStart == null ||
        _currentSessionBookId == null ||
        _currentSessionChapterId == null) {
      return;
    }

    final startedAt = _currentSessionStart!;
    final endedAt = DateTime.now().toUtc();
    final durationSeconds = endedAt.difference(startedAt).inSeconds;
    final bookId = _currentSessionBookId!;
    final chapterId = _currentSessionChapterId!;

    // 현재 세션 초기화
    _currentSessionStart = null;
    _currentSessionBookId = null;
    _currentSessionChapterId = null;

    // 1초 미만 세션은 무시
    if (durationSeconds < 1) return;

    try {
      final deviceId = await _getDeviceId();
      final uri = AppConfig.apiUri('/analytics/play-session');
      await _client.post(
        uri,
        headers: _headers,
        body: json.encode({
          'device_id': deviceId,
          'book_id': bookId,
          'chapter_id': chapterId,
          'started_at': startedAt.toIso8601String(),
          'ended_at': endedAt.toIso8601String(),
          'duration_seconds': durationSeconds,
          'completed': completed,
        }),
      );
    } catch (e) {
      _log.warning('Play session record error', error: e);
    }
  }

  void dispose() {
    _client.close();
  }
}
