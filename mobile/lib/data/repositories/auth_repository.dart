import 'dart:async';
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../../core/constants/app_config.dart';
import '../../core/utils/logger.dart';
import '../../services/accessibility_feedback_service.dart';
import '../services/api_service.dart';

const _log = AppLogger('AuthRepository');

class AuthRepository {
  static const String _tokenKey = 'auth_token';
  static const String _userKey = 'user_data';
  static const String _sessionStorageKey = 'secure_auth_session_v1';

  final ApiService _apiService;
  final SharedPreferences _prefs;
  final FlutterSecureStorage _secureStorage;
  final AccessibilityFeedbackService _accessibilityFeedback;

  User? _currentUser;
  AuthSession? _currentSession;
  final _userController = StreamController<User?>.broadcast();
  final _sessionController = StreamController<AuthSession?>.broadcast();

  AuthRepository({
    required ApiService apiService,
    required SharedPreferences prefs,
    required FlutterSecureStorage secureStorage,
    required AccessibilityFeedbackService accessibilityFeedback,
  })  : _apiService = apiService,
        _prefs = prefs,
        _secureStorage = secureStorage,
        _accessibilityFeedback = accessibilityFeedback {
    _initializeAuth();
  }

  Stream<User?> get userStream => _userController.stream;
  Stream<AuthSession?> get sessionStream => _sessionController.stream;
  User? get currentUser => _currentUser;
  AuthSession? get currentSession => _currentSession;
  bool get isLoggedIn => _currentSession?.isValid ?? false;

  Future<void> _initializeAuth() async {
    if (AppConfig.authBypassEnabled) {
      await _enableGuestMode();
      return;
    }

    await _restoreSessionFromStorage();
    await _restoreUserFromPrefs();

    if (isLoggedIn && _currentUser == null) {
      try {
        await refreshUserProfile();
      } catch (e, st) {
        _log.warning('프로필 로드 실패 (추후 로그인 시 재시도)', error: e, stackTrace: st);
      }
    }
  }

  Future<void> _enableGuestMode() async {
    // 게스트 모드: 네트워크 호출 없이 즉시 세션/사용자 구성
    final now = DateTime.now().toUtc();
    final session = AuthSession(
      accessToken: 'guest-token',
      tokenType: 'bearer',
      issuedAt: now,
      expiresAt: now.add(const Duration(days: 365)),
      scope: 'guest',
      username: 'guest',
    );
    _setSession(session);
    // 게스트 모드에서는 ApiService에 토큰을 주입하지 않음(백엔드 우회 플래그 사용)
    final user = User(
      id: 'guest',
      name: 'Guest User',
      email: 'dev@example.com',
      status: UserStatus.approved,
      scope: 'guest',
    );
    await _prefs.setString(_userKey, _userToString(user));
    _setCurrentUser(user);
  }

  Future<void> _restoreSessionFromStorage() async {
    try {
      final storedSession = await _secureStorage.read(key: _sessionStorageKey);

      if (storedSession == null) {
        // 레거시 SharedPreferences 토큰이 남아있는 경우 마이그레이션
        final legacyToken = _prefs.getString(_tokenKey);
        if (legacyToken != null && legacyToken.isNotEmpty) {
          final now = DateTime.now().toUtc();
          final migratedSession = AuthSession(
            accessToken: legacyToken,
            tokenType: 'bearer',
            issuedAt: now,
            expiresAt: now.add(const Duration(hours: 1)),
          );
          await _persistSession(migratedSession);
          _apiService.setAuthToken(migratedSession.accessToken);
          _setSession(migratedSession);
          await _prefs.remove(_tokenKey);
        }
        return;
      }

      final sessionMap = json.decode(storedSession) as Map<String, dynamic>;
      final session = AuthSession.fromStorageJson(sessionMap);

      if (session.isExpired) {
        await _secureStorage.delete(key: _sessionStorageKey);
        _setSession(null);
        return;
      }

      _apiService.setAuthToken(session.accessToken);
      _setSession(session);
    } catch (e, st) {
      _log.warning('세션 복원 실패', error: e, stackTrace: st);
      await _secureStorage.delete(key: _sessionStorageKey);
      _setSession(null);
    }
  }

  Future<void> _restoreUserFromPrefs() async {
    final userJson = _prefs.getString(_userKey);
    if (userJson == null) {
      _userController.add(_currentUser);
      return;
    }

    try {
      final userData = User.fromJson({..._parseUserJson(userJson)});
      _setCurrentUser(userData);
    } catch (e, st) {
      _log.warning('사용자 정보 복원 실패', error: e, stackTrace: st);
      await _prefs.remove(_userKey);
      _setCurrentUser(null);
    }
  }

  Map<String, dynamic> _parseUserJson(String userJson) {
    try {
      final decoded = json.decode(userJson);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
    } catch (e) {
      _log.debug('JSON 파싱 실패, 레거시 형식 시도', error: e);
    }

    try {
      final Map<String, dynamic> parsed = {};
      final parts = userJson.split('|');
      if (parts.length >= 4) {
        parsed['id'] = parts[0];
        parsed['name'] = parts[1];
        parsed['email'] = parts[2];
        parsed['status'] = parts[3];
      }
      return parsed;
    } catch (e, st) {
      _log.warning('레거시 사용자 데이터 파싱 실패', error: e, stackTrace: st);
      return {};
    }
  }

  String _userToString(User user) {
    return json.encode(user.toStorageJson());
  }

  void _setCurrentUser(User? user) {
    _currentUser = user;
    if (!_userController.isClosed) {
      _userController.add(_currentUser);
    }
  }

  void _setSession(AuthSession? session) {
    _currentSession = session;
    if (!_sessionController.isClosed) {
      _sessionController.add(_currentSession);
    }
  }

  Future<void> handleUnauthorized({String? message, String? origin}) async {
    final alreadyCleared = _currentSession == null && _currentUser == null;
    await clearAuth();

    if (alreadyCleared) {
      return;
    }

    final alertMessage = message ?? '세션이 만료되었습니다. 다시 로그인해주세요.';
    await _accessibilityFeedback.warn(alertMessage);
  }

  Future<void> _syncSessionWithUser(User user) async {
    final session = _currentSession;
    if (session == null) return;

    final updated = session.copyWith(
      username: user.name.isNotEmpty ? user.name : session.username,
      scope: user.scope ?? session.scope,
    );

    final isSame =
        updated.accessToken == session.accessToken &&
        updated.tokenType == session.tokenType &&
        updated.expiresAt == session.expiresAt &&
        updated.scope == session.scope &&
        updated.username == session.username;

    if (isSame) return;

    _setSession(updated);
    await _persistSession(updated);
  }

  Future<AuthResponse> register({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiService.register(
        name: name,
        email: email,
        password: password,
      );

      return AuthResponse.fromJson(response);
    } catch (e) {
      rethrow;
    }
  }

  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    if (AppConfig.authBypassEnabled) {
      // 게스트 모드에서는 즉시 성공 응답 구성
      final now = DateTime.now().toUtc();
      final session = AuthSession(
        accessToken: 'guest-token',
        tokenType: 'bearer',
        issuedAt: now,
        expiresAt: now.add(const Duration(days: 365)),
        scope: 'guest',
        username: email,
      );
      _setSession(session);
      final user = User(
        id: 'guest',
        name: 'Guest User',
        email: email,
        status: UserStatus.approved,
        scope: 'guest',
      );
      await _prefs.setString(_userKey, _userToString(user));
      _setCurrentUser(user);
      return AuthResponse(message: 'guest', user: user, session: session);
    }

    try {
      final response = await _apiService.login(
        email: email,
        password: password,
      );

      final authResponse = AuthResponse.fromJson(response);
      final session = authResponse.session;

      if (session == null) {
        throw const ApiException(
          message: '로그인 응답에서 토큰 정보를 찾을 수 없습니다.',
          statusCode: -1,
        );
      }

      await _persistSession(session);
      _apiService.setAuthToken(session.accessToken);
      _setSession(session);

      User? resolvedUser = authResponse.user;

      if (resolvedUser != null) {
        await _prefs.setString(_userKey, _userToString(resolvedUser));
        _setCurrentUser(resolvedUser);
        await _syncSessionWithUser(resolvedUser);
      } else {
        resolvedUser = await refreshUserProfile();
      }

      await _prefs.remove(_tokenKey);

      return AuthResponse(
        message: authResponse.message,
        user: resolvedUser,
        session: session,
      );
    } catch (e) {
      if (e is ApiException) rethrow;
      if (e is FormatException) {
        throw const ApiException(
          message: '로그인 응답 처리 중 오류가 발생했습니다.',
          statusCode: -1,
        );
      }
      throw ApiException(
        message: '로그인 처리 중 알 수 없는 오류가 발생했습니다.',
        statusCode: -1,
        details: e,
      );
    }
  }

  Future<void> logout() async {
    await clearAuth();
  }

  Future<void> clearAuth() async {
    if (AppConfig.authBypassEnabled) {
      // 게스트 모드에서는 간단 초기화만 수행
      _setCurrentUser(null);
      _setSession(null);
      return;
    }
    _currentUser = null;
    _userController.add(null);
    _setSession(null);

    await _prefs.remove(_tokenKey);
    await _prefs.remove(_userKey);
    await _secureStorage.delete(key: _sessionStorageKey);

    _apiService.clearAuthToken();
  }

  Future<User?> refreshUserProfile() async {
    if (AppConfig.authBypassEnabled) {
      return _currentUser;
    }
    if (!isLoggedIn) return null;

    try {
      final response = await _apiService.getCurrentUser();
      final user = User.fromJson(response);

      // 사용자 정보 업데이트
      await _prefs.setString(_userKey, _userToString(user));
      _setCurrentUser(user);
      await _syncSessionWithUser(user);

      return user;
    } catch (e) {
      if (e is ApiException && (e.isUnauthorized || e.isForbidden)) {
        await handleUnauthorized(message: '세션이 만료되었습니다. 다시 로그인해주세요.');
        rethrow;
      }
      if (e is FormatException) {
        throw const ApiException(
          message: '사용자 정보를 불러오는 데 실패했습니다.',
          statusCode: -1,
        );
      }
      rethrow;
    }
  }

  void dispose() {
    _userController.close();
    _apiService.dispose();
    _sessionController.close();
  }

  Future<void> _persistSession(AuthSession session) async {
    final sessionJson = json.encode(session.toJson());
    await _secureStorage.write(key: _sessionStorageKey, value: sessionJson);
  }
}
