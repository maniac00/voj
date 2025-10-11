import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../core/constants/app_config.dart';
import '../models/book_model.dart';

/// 오디오 관련 API 서비스
class AudioService {
  final http.Client _client;
  final String _baseUrl;
  String? _authToken;

  AudioService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = _sanitizeBaseUrl(baseUrl ?? AppConfig.apiBaseUrl);

  void setAuthToken(String token) {
    _authToken = token;
  }

  void clearAuthToken() {
    _authToken = null;
  }

  /// 책에 포함된 챕터 목록을 조회한다.
  Future<List<AudioChapter>> getChapters({
    required String bookId,
    String? status,
  }) async {
    try {
      final uri = _buildUri('/audio/$bookId/chapters', queryParameters: {
        if (status != null) 'status': status,
      });

      final response = await _client.get(uri, headers: _headers);
      final Map<String, dynamic> data = await _handleResponse(response);

      final chaptersRaw = data['chapters'] as List<dynamic>? ?? data['data'] as List<dynamic>?;
      if (chaptersRaw == null) {
        return const [];
      }

      return chaptersRaw
          .whereType<Map<String, dynamic>>()
          .map(AudioChapter.fromJson)
          .toList();
    } on SocketException {
      throw const AudioServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (error) {
      if (error is AudioServiceException) rethrow;
      throw const AudioServiceException(
        message: '챕터 목록을 불러오는 데 실패했습니다',
        statusCode: -1,
      );
    }
  }

  /// 챕터 상세 정보를 조회한다.
  Future<AudioChapter> getChapter({
    required String bookId,
    required String chapterId,
  }) async {
    try {
      final uri = _buildUri('/audio/$bookId/chapters/$chapterId');
      final response = await _client.get(uri, headers: _headers);
      final data = await _handleResponse(response);
      final payload = data['chapter'] ?? data;
      return AudioChapter.fromJson(Map<String, dynamic>.from(payload as Map<String, dynamic>));
    } on SocketException {
      throw const AudioServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (error) {
      if (error is AudioServiceException) rethrow;
      throw const AudioServiceException(
        message: '챕터 정보를 불러오는 데 실패했습니다',
        statusCode: -1,
      );
    }
  }

  /// 챕터 스트리밍 URL을 발급받는다.
  Future<StreamingUrl> getStreamingUrl({
    required String bookId,
    required String chapterId,
  }) async {
    try {
      final uri = _buildUri('/audio/$bookId/chapters/$chapterId/stream');
      final response = await _client.get(uri, headers: _headers);
      final data = await _handleResponse(response);
      return StreamingUrl.fromJson(data);
    } on SocketException {
      throw const AudioServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (error) {
      if (error is AudioServiceException) rethrow;
      throw const AudioServiceException(
        message: '스트리밍 URL을 발급받지 못했습니다',
        statusCode: -1,
      );
    }
  }

  /// 재생 진행률을 서버에 저장한다.
  Future<void> updatePlaybackProgress({
    required String bookId,
    required String chapterId,
    required int position,
    required int duration,
  }) async {
    try {
      final uri = _buildUri('/audio/$bookId/chapters/$chapterId/progress');
      final response = await _client.post(
        uri,
        headers: _headers,
        body: json.encode({
          'position': position,
          'duration': duration,
        }),
      );

      await _handleResponse(response);
    } on SocketException {
      throw const AudioServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (error) {
      if (error is AudioServiceException) rethrow;
      throw const AudioServiceException(
        message: '재생 진행률을 저장하지 못했습니다',
        statusCode: -1,
      );
    }
  }

  /// 마지막 재생 위치를 조회한다.
  Future<PlaybackPosition?> getPlaybackPosition({
    required String bookId,
    required String chapterId,
  }) async {
    try {
      final uri = _buildUri('/audio/$bookId/chapters/$chapterId/position');
      final response = await _client.get(uri, headers: _headers);
      final data = await _handleResponse(response);

      if (data.isEmpty) {
        return null;
      }

      return PlaybackPosition.fromJson(data);
    } on SocketException {
      throw const AudioServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (error) {
      if (error is AudioServiceException) rethrow;
      throw const AudioServiceException(
        message: '재생 위치를 불러오지 못했습니다',
        statusCode: -1,
      );
    }
  }

  /// 재생 기록(히스토리)을 조회한다.
  Future<List<PlaybackHistory>> getPlaybackHistory({required String bookId}) async {
    try {
      final uri = _buildUri('/audio/$bookId/history');
      final response = await _client.get(uri, headers: _headers);
      final data = await _handleResponse(response);
      final history = data['playHistory'] as List<dynamic>? ?? [];

      return history
          .whereType<Map<String, dynamic>>()
          .map(PlaybackHistory.fromJson)
          .toList();
    } on SocketException {
      throw const AudioServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (error) {
      if (error is AudioServiceException) rethrow;
      throw const AudioServiceException(
        message: '재생 기록을 불러오지 못했습니다',
        statusCode: -1,
      );
    }
  }

  Uri _buildUri(String path, {Map<String, dynamic>? queryParameters}) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    final uri = Uri.parse('$_baseUrl$normalizedPath');
    if (queryParameters == null) {
      return uri;
    }

    final sanitized = queryParameters.map((key, value) => MapEntry(key, value.toString()));
    return uri.replace(queryParameters: sanitized);
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  Future<Map<String, dynamic>> _handleResponse(http.Response response) async {
    final body = utf8.decode(response.bodyBytes);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      final decoded = json.decode(body);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
      return {'data': decoded};
    }

    final errorData = json.decode(body) as Map<String, dynamic>;
    throw AudioServiceException(
      message: errorData['message'] as String? ?? errorData['detail'] as String? ?? 'Unknown error',
      statusCode: response.statusCode,
      details: errorData['details'],
    );
  }

  static String _sanitizeBaseUrl(String value) {
    final sanitized = value.replaceFirst(RegExp(r'/+$'), '');
    return sanitized.isEmpty ? AppConfig.apiBaseUrl : sanitized;
  }

  void dispose() {
    _client.close();
  }
}

class StreamingUrl {
  final String streamingUrl;
  final DateTime? expiresAt;
  final int? duration;

  const StreamingUrl({
    required this.streamingUrl,
    this.expiresAt,
    this.duration,
  });

  factory StreamingUrl.fromJson(Map<String, dynamic> json) {
    final url = json['streaming_url'] as String? ?? json['streamingUrl'] as String? ?? '';
    final expires = json['expires_at'] as String? ?? json['expiresAt'] as String?;

    return StreamingUrl(
      streamingUrl: url,
      expiresAt: expires != null && expires.isNotEmpty ? DateTime.tryParse(expires) : null,
      duration: json['duration'] as int?,
    );
  }

  String get absoluteUrl {
    final parsed = Uri.tryParse(streamingUrl);
    if (parsed != null && parsed.hasScheme) {
      return streamingUrl;
    }
    // Resolve against API base URL (may include "/api/v1").
    // This prevents duplicate "/api/v1" when server returns "/api/v1/files/...".
    final base = Uri.parse(AppConfig.apiBaseUrl);
    return base.resolve(streamingUrl).toString();
  }
}

class PlaybackPosition {
  final int position;
  final int duration;
  final DateTime? lastPlayedAt;

  const PlaybackPosition({
    required this.position,
    required this.duration,
    this.lastPlayedAt,
  });

  factory PlaybackPosition.fromJson(Map<String, dynamic> json) {
    return PlaybackPosition(
      position: json['position'] as int? ?? 0,
      duration: json['duration'] as int? ?? 0,
      lastPlayedAt: (json['last_played_at'] ?? json['lastPlayedAt']) != null
          ? DateTime.tryParse(json['last_played_at'] as String? ?? json['lastPlayedAt'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'position': position,
      'duration': duration,
      if (lastPlayedAt != null) 'lastPlayedAt': lastPlayedAt!.toIso8601String(),
    };
  }
}

class PlaybackHistory {
  final String id;
  final String bookId;
  final String chapterId;
  final int position;
  final int duration;
  final DateTime lastPlayedAt;
  final AudioChapter chapter;

  const PlaybackHistory({
    required this.id,
    required this.bookId,
    required this.chapterId,
    required this.position,
    required this.duration,
    required this.lastPlayedAt,
    required this.chapter,
  });

  factory PlaybackHistory.fromJson(Map<String, dynamic> json) {
    return PlaybackHistory(
      id: json['id'] as String? ?? '',
      bookId: json['book_id'] as String? ?? json['bookId'] as String? ?? '',
      chapterId: json['chapter_id'] as String? ?? json['chapterId'] as String? ?? '',
      position: json['position'] as int? ?? 0,
      duration: json['duration'] as int? ?? 0,
      lastPlayedAt: DateTime.parse(json['last_played_at'] as String? ?? json['lastPlayedAt'] as String? ?? DateTime.now().toIso8601String()),
      chapter: AudioChapter.fromJson(
        Map<String, dynamic>.from(json['chapter'] as Map? ?? json['audioFile'] as Map? ?? {}),
      ),
    );
  }
}

class AudioServiceException implements Exception {
  final String message;
  final int statusCode;
  final dynamic details;

  const AudioServiceException({
    required this.message,
    required this.statusCode,
    this.details,
  });

  @override
  String toString() => 'AudioServiceException: $message (Status: $statusCode)';

  bool get isNetworkError => statusCode == 0;
  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;
  bool get isValidationError => statusCode == 400;
}