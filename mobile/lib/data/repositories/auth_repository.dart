import 'dart:async';
import 'dart:convert';
import 'package:firebase_auth/firebase_auth.dart' as fb;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../../core/constants/app_config.dart';
import '../../core/utils/logger.dart';
import '../../services/accessibility_feedback_service.dart';
import '../services/api_service.dart';

const _log = AppLogger('AuthRepository');

class AuthRepository {
  static const String _userKey = 'user_data';
  static const String _refreshTokenStorageKey = 'secure_refresh_token_v2';
  static const String _legacySessionStorageKey = 'secure_auth_session_v1';
  static const String _deviceIdKey = 'voj_device_id';

  final ApiService _apiService;
  final SharedPreferences _prefs;
  final FlutterSecureStorage _secureStorage;
  final AccessibilityFeedbackService _accessibilityFeedback;

  final fb.FirebaseAuth _firebaseAuth = fb.FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    serverClientId:
        '731128991571-evuscn1g07f0lpa3fjhj8faf1mrb239p.apps.googleusercontent.com',
  );

  User? _currentUser;
  AuthSession? _currentSession;
  String? _refreshToken;

  final _userController = StreamController<User?>.broadcast();
  final _sessionController = StreamController<AuthSession?>.broadcast();
  final Completer<void> _initializedCompleter = Completer<void>();

  AuthRepository({
    required ApiService apiService,
    required SharedPreferences prefs,
    required FlutterSecureStorage secureStorage,
    required AccessibilityFeedbackService accessibilityFeedback,
  }) : _apiService = apiService,
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
  Future<void> get initialized => _initializedCompleter.future;
  bool get isInitialized => _initializedCompleter.isCompleted;

  Future<void> _initializeAuth() async {
    try {
      if (AppConfig.authBypassEnabled) {
        await _enableGuestMode();
        return;
      }

      final autoLogin = _prefs.getBool('auto_login') ?? true;
      if (!autoLogin) {
        _setSession(null);
        _setCurrentUser(null);
        _apiService.clearAuthToken();
        return;
      }

      final refreshed = await refreshToken();
      if (!refreshed) {
        _setSession(null);
        _setCurrentUser(null);
      }
    } catch (e, st) {
      _log.warning('인증 초기화 실패', error: e, stackTrace: st);
      _setSession(null);
      _setCurrentUser(null);
      _apiService.clearAuthToken();
    } finally {
      if (!_initializedCompleter.isCompleted) {
        _initializedCompleter.complete();
      }
    }
  }

  Future<void> _enableGuestMode() async {
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
    final user = User(
      id: 'guest',
      name: 'Guest User',
      email: 'dev@example.com',
      status: UserStatus.approved,
      scope: 'guest',
    );
    await _prefs.setString(_userKey, json.encode(user.toStorageJson()));
    _setCurrentUser(user);
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

  Future<String> _getOrCreateDeviceId() async {
    final existing = _prefs.getString(_deviceIdKey);
    if (existing != null && existing.isNotEmpty) {
      return existing;
    }

    final nowMicros = DateTime.now().microsecondsSinceEpoch;
    final generated =
        '${nowMicros.toRadixString(16)}-${DateTime.now().millisecondsSinceEpoch.toRadixString(16)}-${nowMicros.hashCode.abs().toRadixString(16)}';
    await _prefs.setString(_deviceIdKey, generated);
    return generated;
  }

  UserStatus _parseUserStatus(String? status) {
    switch (status) {
      case 'approved':
        return UserStatus.approved;
      case 'suspended':
        return UserStatus.suspended;
      case 'pending':
      default:
        return UserStatus.pending;
    }
  }

  User _buildUserFromAuthPayload(Map<String, dynamic> response) {
    final userId = (response['user_id'] ?? response['id'] ?? '').toString();
    final email = response['email'] as String?;
    final displayName = response['display_name'] as String?;
    final role = response['role'] as String? ?? response['scope'] as String?;

    return User(
      id: userId,
      name: displayName ?? email ?? '',
      email: email,
      status: _parseUserStatus(response['status'] as String?),
      scope: role,
    );
  }

  Future<void> _applyMobileAuthPayload(Map<String, dynamic> response) async {
    final now = DateTime.now().toUtc();
    final session = AuthSession.fromLoginJson(response, issuedAt: now);

    final refreshToken = response['refresh_token'] as String?;
    if (refreshToken == null || refreshToken.isEmpty) {
      throw const ApiException(
        message: '로그인 응답에 refresh_token이 없습니다.',
        statusCode: -1,
      );
    }

    final user = _buildUserFromAuthPayload(response);

    _apiService.setAuthToken(session.accessToken);
    _setSession(session);

    _refreshToken = refreshToken;
    await _secureStorage.write(
      key: _refreshTokenStorageKey,
      value: refreshToken,
    );

    await _prefs.setString(_userKey, json.encode(user.toStorageJson()));
    _setCurrentUser(user);
  }

  /// Google 소셜 로그인 → Firebase → 백엔드 모바일 세션 발급
  Future<AuthResponse> signInWithGoogle() async {
    try {
      _log.info('[로그인 1/5] Google Sign-In 시작...');
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        throw const ApiException(
          message: 'Google 로그인이 취소되었습니다.',
          statusCode: -1,
        );
      }
      _log.info('[로그인 2/5] Google 계정 선택 완료: ${googleUser.email}');

      final googleAuth = await googleUser.authentication;
      _log.info('[로그인 2/5] Google 인증 토큰 획득 완료');

      _log.info('[로그인 3/5] Firebase 인증 시작...');
      final credential = fb.GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _firebaseAuth.signInWithCredential(
        credential,
      );

      return await _completeFirebaseLogin(userCredential.user);
    } on fb.FirebaseAuthException catch (e) {
      _log.severe('[로그인 실패] Firebase 오류: ${e.code} - ${e.message}');
      throw ApiException(
        message: '[단계3 Firebase] ${e.code}: ${e.message}',
        statusCode: -1,
      );
    } on ApiException catch (e) {
      _log.severe('[로그인 실패] API 오류: ${e.message}');
      rethrow;
    } catch (e, st) {
      _log.severe(
        '[로그인 실패] 예외: ${e.runtimeType}: $e',
        error: e,
        stackTrace: st,
      );
      throw ApiException(message: '[${e.runtimeType}] $e', statusCode: -1);
    }
  }

  /// Apple 소셜 로그인 → Firebase → 백엔드 모바일 세션 발급 (iOS 전용)
  Future<AuthResponse> signInWithApple() async {
    try {
      _log.info('[로그인 1/5] Apple Sign-In 시작...');
      final appleProvider = fb.AppleAuthProvider()
        ..addScope('email')
        ..addScope('name');

      _log.info('[로그인 3/5] Firebase 인증 시작...');
      final userCredential = await _firebaseAuth.signInWithProvider(
        appleProvider,
      );

      return await _completeFirebaseLogin(userCredential.user);
    } on fb.FirebaseAuthException catch (e) {
      if (e.code == 'canceled' || e.code == 'web-context-canceled') {
        throw const ApiException(
          message: 'Apple 로그인이 취소되었습니다.',
          statusCode: -1,
        );
      }
      _log.severe('[로그인 실패] Firebase 오류: ${e.code} - ${e.message}');
      throw ApiException(
        message: '[단계3 Firebase] ${e.code}: ${e.message}',
        statusCode: -1,
      );
    } on ApiException catch (e) {
      _log.severe('[로그인 실패] API 오류: ${e.message}');
      rethrow;
    } catch (e, st) {
      _log.severe(
        '[로그인 실패] 예외: ${e.runtimeType}: $e',
        error: e,
        stackTrace: st,
      );
      throw ApiException(message: '[${e.runtimeType}] $e', statusCode: -1);
    }
  }

  /// Firebase 인증 완료 후 공통 처리: ID 토큰 → 백엔드 모바일 세션 발급
  Future<AuthResponse> _completeFirebaseLogin(fb.User? fbUser) async {
    if (fbUser == null) {
      throw const ApiException(
        message: 'Firebase 인증에 실패했습니다.',
        statusCode: -1,
      );
    }
    _log.info('[로그인 3/5] Firebase 인증 성공: ${fbUser.uid}');

    _log.info('[로그인 4/5] Firebase ID 토큰 획득 중...');
    final idToken = await fbUser.getIdToken();
    if (idToken == null) {
      throw const ApiException(
        message: 'Firebase ID 토큰을 가져올 수 없습니다.',
        statusCode: -1,
      );
    }
    _log.info('[로그인 4/5] Firebase ID 토큰 획득 완료');

    final deviceId = await _getOrCreateDeviceId();

    _log.info('[로그인 5/5] 백엔드 모바일 로그인 요청 중...');
    final response = await _apiService.post(
      '/auth/mobile/login',
      body: {'id_token': idToken, 'device_id': deviceId},
    );
    _log.info('[로그인 5/5] 백엔드 모바일 로그인 성공');

    await _applyMobileAuthPayload(response);

    return AuthResponse(
      message: response['is_new_user'] == true ? 'new_user' : 'existing_user',
      user: _currentUser,
      session: _currentSession,
    );
  }

  /// 본인 계정 삭제 (App Store 가이드라인 5.1.1(v))
  /// 서버가 계정·연관 데이터·Firebase 계정을 삭제하면 로컬 세션을 정리한다.
  Future<void> deleteAccount() async {
    await _apiService.delete('/users/me');
    await signOut();
  }

  Future<void> signOut() async {
    try {
      await _firebaseAuth.signOut();
      await _googleSignIn.signOut();
    } catch (e) {
      _log.warning('Firebase/Google 로그아웃 실패', error: e);
    }
    await clearAuth();
  }

  Future<void> logout() async {
    if (!AppConfig.authBypassEnabled) {
      try {
        final refresh =
            _refreshToken ??
            await _secureStorage.read(key: _refreshTokenStorageKey);
        if (refresh != null && refresh.isNotEmpty) {
          final deviceId = await _getOrCreateDeviceId();
          await _apiService.post(
            '/auth/mobile/logout',
            body: {'refresh_token': refresh, 'device_id': deviceId},
          );
        }
      } catch (e) {
        _log.warning('서버 로그아웃 요청 실패', error: e);
      }
    }

    await signOut();
  }

  Future<void> clearAuth() async {
    if (AppConfig.authBypassEnabled) {
      _setCurrentUser(null);
      _setSession(null);
      return;
    }

    _refreshToken = null;
    _setCurrentUser(null);
    _setSession(null);

    await _prefs.remove(_userKey);
    await _secureStorage.delete(key: _legacySessionStorageKey);
    await _secureStorage.delete(key: _refreshTokenStorageKey);

    _apiService.clearAuthToken();
  }

  /// Refresh Token으로 Access Token을 재발급한다.
  /// 성공하면 true, 실패하면 false를 반환한다.
  Future<bool> refreshToken() async {
    if (AppConfig.authBypassEnabled) return true;

    final refresh =
        _refreshToken ??
        await _secureStorage.read(key: _refreshTokenStorageKey);
    if (refresh == null || refresh.isEmpty) {
      _log.info('저장된 Refresh Token 없음');
      return false;
    }

    _refreshToken = refresh;
    final deviceId = await _getOrCreateDeviceId();

    try {
      final response = await _apiService.post(
        '/auth/mobile/refresh',
        body: {'refresh_token': refresh, 'device_id': deviceId},
      );
      await _applyMobileAuthPayload(response);
      _log.info('토큰 갱신 성공');
      return true;
    } catch (e) {
      _log.warning('토큰 갱신 실패', error: e);
      if (e is ApiException && (e.isUnauthorized || e.isForbidden)) {
        await clearAuth();
      }
      return false;
    }
  }

  Future<void> handleUnauthorized({String? message, String? origin}) async {
    final alreadyCleared = _currentSession == null && _currentUser == null;
    await clearAuth();

    if (alreadyCleared) return;

    final alertMessage = message ?? '세션이 만료되었습니다. 다시 로그인해주세요.';
    await _accessibilityFeedback.warn(alertMessage);
  }

  Future<User?> refreshUserProfile() async {
    if (AppConfig.authBypassEnabled) return _currentUser;
    if (!isLoggedIn) return null;

    try {
      final response = await _apiService.getCurrentUser();
      final user = User.fromJson(response);

      await _prefs.setString(_userKey, json.encode(user.toStorageJson()));
      _setCurrentUser(user);

      return user;
    } catch (e) {
      if (e is ApiException && (e.isUnauthorized || e.isForbidden)) {
        await handleUnauthorized(message: '세션이 만료되었습니다. 다시 로그인해주세요.');
        rethrow;
      }
      rethrow;
    }
  }

  void dispose() {
    _userController.close();
    _apiService.dispose();
    _sessionController.close();
  }
}
