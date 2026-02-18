import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:voice_of_juan/core/constants/app_config.dart';
import 'package:voice_of_juan/core/utils/logger.dart';

const _log = AppLogger('ApiService');

class ApiService {
  final http.Client _client;
  final String _baseUrl;
  String? _authToken;

  ApiService({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = _sanitizeBaseUrl(baseUrl ?? AppConfig.apiBaseUrl);

  void setAuthToken(String token) {
    _authToken = token;
  }

  void clearAuthToken() {
    _authToken = null;
  }

  Future<Map<String, dynamic>> request({
    required String method,
    required String path,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? body,
  }) async {
    try {
      final uri = _buildUri(path, queryParameters: queryParameters);
      final response = await _send(method: method, uri: uri, body: body);
      return await _handleResponse(response);
    } on SocketException {
      throw ApiException(message: '네트워크 연결을 확인해주세요', statusCode: 0);
    }
  }

  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? queryParameters}) {
    return request(method: 'GET', path: path, queryParameters: queryParameters);
  }

  Future<Map<String, dynamic>> post(String path, {Map<String, dynamic>? body}) {
    return request(method: 'POST', path: path, body: body);
  }

  Future<Map<String, dynamic>> delete(String path) {
    return request(method: 'DELETE', path: path);
  }

  Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      return await post('/auth/register', body: {
        'name': name,
        'email': email,
        'password': password,
      });
    } on ApiException {
      rethrow;
    } catch (e, st) {
      _log.warning('회원가입 중 오류', error: e, stackTrace: st);
      throw ApiException(message: '회원가입 중 오류가 발생했습니다', statusCode: -1);
    }
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      return await post('/auth/login', body: {
        'email': email,
        'password': password,
      });
    } on ApiException {
      rethrow;
    } catch (e, st) {
      _log.warning('로그인 중 오류', error: e, stackTrace: st);
      throw ApiException(message: '로그인 중 오류가 발생했습니다', statusCode: -1);
    }
  }

  Future<Map<String, dynamic>> getCurrentUser() async {
    try {
      return await get('/auth/me');
    } on ApiException {
      rethrow;
    } catch (e, st) {
      _log.warning('프로필 조회 중 오류', error: e, stackTrace: st);
      throw ApiException(message: '프로필 조회 중 오류가 발생했습니다', statusCode: -1);
    }
  }

  Future<http.Response> _send({
    required String method,
    required Uri uri,
    Map<String, dynamic>? body,
  }) async {
    switch (method) {
      case 'GET':
        return _client.get(uri, headers: _headers);
      case 'POST':
        return _client.post(uri, headers: _headers, body: json.encode(body ?? {}));
      case 'PUT':
        return _client.put(uri, headers: _headers, body: json.encode(body ?? {}));
      case 'PATCH':
        return _client.patch(uri, headers: _headers, body: json.encode(body ?? {}));
      case 'DELETE':
        return _client.delete(uri, headers: _headers);
      default:
        throw UnsupportedError('Unsupported HTTP method: $method');
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

  static String _sanitizeBaseUrl(String value) {
    final sanitized = value.replaceFirst(RegExp(r'/+$'), '');
    return sanitized.isEmpty ? AppConfig.apiBaseUrl : sanitized;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  Future<Map<String, dynamic>> _handleResponse(http.Response response) async {
    final body = utf8.decode(response.bodyBytes);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return json.decode(body) as Map<String, dynamic>;
    }

    final errorData = json.decode(body) as Map<String, dynamic>;
    throw ApiException(
      message: errorData['message'] as String? ?? errorData['detail'] as String? ?? errorData['error'] as String? ?? 'Unknown error',
      statusCode: response.statusCode,
      details: errorData['details'],
    );
  }

  void dispose() {
    _client.close();
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  final dynamic details;

  const ApiException({
    required this.message,
    required this.statusCode,
    this.details,
  });

  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';

  bool get isNetworkError => statusCode == 0;
  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isValidationError => statusCode == 400;
}
