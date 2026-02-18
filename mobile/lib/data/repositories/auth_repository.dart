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
  static const String _sessionStorageKey = 'secure_auth_session_v1';

  final ApiService _apiService;
  final SharedPreferences _prefs;
  final FlutterSecureStorage _secureStorage;
  final AccessibilityFeedbackService _accessibilityFeedback;

  final fb.FirebaseAuth _firebaseAuth = fb.FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    serverClientId: '731128991571-evuscn1g07f0lpa3fjhj8faf1mrb239p.apps.googleusercontent.com',
  );

  User? _currentUser;
  AuthSession? _currentSession;
  final _userController = StreamController<User?>.broadcast();
  final _sessionController = StreamController<AuthSession?>.broadcast();

  StreamSubscription<fb.User?>? _idTokenSubscription;

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

    // Firebase idTokenChanges로 자동 토큰 갱신
    _idTokenSubscription = _firebaseAuth.idTokenChanges().listen((fbUser) async {
      if (fbUser != null) {
        final idToken = await fbUser.getIdToken();
        if (idToken != null) {
          _apiService.setAuthToken(idToken);
          final now = DateTime.now().toUtc();
          final session = AuthSession(
            accessToken: idToken,
            tokenType: 'bearer',
            issuedAt: now,
            expiresAt: now.add(const Duration(hours: 48)),
            username: fbUser.displayName ?? fbUser.email,
          );
          _setSession(session);
          await _persistSession(session);

          // broadcast stream은 구독 전 이벤트를 유실하므로,
          // 세션 갱신 시 사용자 데이터도 다시 emit
          if (_currentUser != null) {
            _setCurrentUser(_currentUser!);
          } else {
            await _restoreUserFromPrefs();
          }
        }
      } else {
        _setSession(null);
        _setCurrentUser(null);
      }
    });

    // 기존 세션 복원
    await _restoreUserFromPrefs();

    // Firebase 현재 사용자가 있으면 토큰 갱신
    final fbUser = _firebaseAuth.currentUser;
    if (fbUser != null) {
      try {
        final idToken = await fbUser.getIdToken(true);
        if (idToken != null) {
          _apiService.setAuthToken(idToken);
        }
      } catch (e) {
        _log.warning('토큰 갱신 실패', error: e);
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

  Future<void> _restoreUserFromPrefs() async {
    final userJson = _prefs.getString(_userKey);
    if (userJson == null) {
      _userController.add(_currentUser);
      return;
    }

    try {
      final userData = json.decode(userJson) as Map<String, dynamic>;
      final user = User.fromJson(userData);
      _setCurrentUser(user);
    } catch (e, st) {
      _log.warning('사용자 정보 복원 실패', error: e, stackTrace: st);
      await _prefs.remove(_userKey);
      _setCurrentUser(null);
    }
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

  /// Google 소셜 로그인 → Firebase → 백엔드 등록/로그인
  Future<AuthResponse> signInWithGoogle() async {
    try {
      // 1. Google Sign-In
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

      // 2. Firebase signInWithCredential
      _log.info('[로그인 3/5] Firebase 인증 시작...');
      final credential = fb.GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential = await _firebaseAuth.signInWithCredential(credential);
      final fbUser = userCredential.user;
      if (fbUser == null) {
        throw const ApiException(
          message: 'Firebase 인증에 실패했습니다.',
          statusCode: -1,
        );
      }
      _log.info('[로그인 3/5] Firebase 인증 성공: ${fbUser.uid}');

      // 3. Firebase ID 토큰 획득
      _log.info('[로그인 4/5] Firebase ID 토큰 획득 중...');
      final idToken = await fbUser.getIdToken();
      if (idToken == null) {
        throw const ApiException(
          message: 'Firebase ID 토큰을 가져올 수 없습니다.',
          statusCode: -1,
        );
      }
      _log.info('[로그인 4/5] Firebase ID 토큰 획득 완료');

      _apiService.setAuthToken(idToken);

      // 4. 백엔드에 Firebase 로그인 전송
      _log.info('[로그인 5/5] 백엔드 로그인 요청 중...');
      final response = await _apiService.post('/auth/firebase-login', body: {
        'id_token': idToken,
      });
      _log.info('[로그인 5/5] 백엔드 로그인 성공');

      // 5. 사용자 정보 구성
      final userStatus = _parseUserStatus(response['status'] as String?);
      final user = User(
        id: (response['user_id'] ?? '').toString(),
        name: response['display_name'] as String? ?? fbUser.displayName ?? '',
        email: response['email'] as String? ?? fbUser.email ?? '',
        status: userStatus,
        scope: response['role'] as String?,
      );

      final now = DateTime.now().toUtc();
      final session = AuthSession(
        accessToken: idToken,
        tokenType: 'bearer',
        issuedAt: now,
        expiresAt: now.add(const Duration(hours: 48)),
        username: user.name,
      );

      await _persistSession(session);
      _setSession(session);
      await _prefs.setString(_userKey, json.encode(user.toStorageJson()));
      _setCurrentUser(user);

      return AuthResponse(
        message: response['is_new_user'] == true ? 'new_user' : 'existing_user',
        user: user,
        session: session,
      );
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
      _log.severe('[로그인 실패] 예외: ${e.runtimeType}: $e', error: e, stackTrace: st);
      throw ApiException(
        message: '[${e.runtimeType}] $e',
        statusCode: -1,
      );
    }
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
    await signOut();
  }

  Future<void> clearAuth() async {
    if (AppConfig.authBypassEnabled) {
      _setCurrentUser(null);
      _setSession(null);
      return;
    }
    _currentUser = null;
    _userController.add(null);
    _setSession(null);

    await _prefs.remove(_userKey);
    await _secureStorage.delete(key: _sessionStorageKey);

    _apiService.clearAuthToken();
  }

  /// Firebase 토큰을 강제 갱신하고 ApiService에 설정한다.
  /// 성공하면 true, 실패하면 false를 반환한다.
  Future<bool> refreshToken() async {
    if (AppConfig.authBypassEnabled) return true;

    final fbUser = _firebaseAuth.currentUser;
    if (fbUser == null) {
      _log.warning('토큰 갱신 실패: Firebase 사용자 없음');
      return false;
    }

    try {
      final idToken = await fbUser.getIdToken(true); // forceRefresh
      if (idToken == null) return false;

      _apiService.setAuthToken(idToken);
      final now = DateTime.now().toUtc();
      final session = AuthSession(
        accessToken: idToken,
        tokenType: 'bearer',
        issuedAt: now,
        expiresAt: now.add(const Duration(hours: 48)),
        username: fbUser.displayName ?? fbUser.email,
      );
      _setSession(session);
      await _persistSession(session);
      _log.info('토큰 강제 갱신 성공');
      return true;
    } catch (e) {
      _log.warning('토큰 강제 갱신 실패', error: e);
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
    _idTokenSubscription?.cancel();
    _userController.close();
    _apiService.dispose();
    _sessionController.close();
  }

  Future<void> _persistSession(AuthSession session) async {
    final sessionJson = json.encode(session.toJson());
    await _secureStorage.write(key: _sessionStorageKey, value: sessionJson);
  }
}
