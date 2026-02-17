import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/utils/logger.dart';
import '../../data/models/user_model.dart';
import '../../data/repositories/auth_repository.dart';
import '../../data/services/api_service.dart';
import '../../services/accessibility_feedback_service.dart';
import '../../core/constants/app_config.dart';

const _log = AppLogger('AuthProvider');

// API 서비스 프로바이더
final apiServiceProvider = Provider<ApiService>((ref) {
  return ApiService();
});

// SharedPreferences 프로바이더
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('SharedPreferences must be initialized');
});

// 접근성 피드백 서비스 프로바이더
final accessibilityFeedbackProvider = Provider<AccessibilityFeedbackService>((ref) {
  return const AccessibilityFeedbackService();
});

// SecureStorage 프로바이더
final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

// 인증 저장소 프로바이더
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  final prefs = ref.watch(sharedPreferencesProvider);
  final accessibility = ref.watch(accessibilityFeedbackProvider);
  final secureStorage = ref.watch(secureStorageProvider);
  final repo = AuthRepository(
    apiService: apiService,
    prefs: prefs,
    secureStorage: secureStorage,
    accessibilityFeedback: accessibility,
  );
  ref.onDispose(() => repo.dispose());
  return repo;
});

// 현재 사용자 프로바이더
final currentUserProvider = StreamProvider<User?>((ref) {
  final authRepo = ref.watch(authRepositoryProvider);
  return authRepo.userStream;
});

// 현재 인증 세션 프로바이더
final authSessionProvider = StreamProvider<AuthSession?>((ref) {
  final authRepo = ref.watch(authRepositoryProvider);
  return authRepo.sessionStream;
});

// 인증 상태 프로바이더
final isLoggedInProvider = Provider<bool>((ref) {
  if (AppConfig.authBypassEnabled) {
    return true;
  }
  final sessionAsync = ref.watch(authSessionProvider);
  return sessionAsync.when(
    data: (session) => session?.isValid ?? false,
    loading: () => false,
    error: (_, __) => false,
  );
});

// 인증 컨트롤러 프로바이더
final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) {
    final authRepo = ref.watch(authRepositoryProvider);
    return AuthController(authRepo);
  },
);

class AuthController extends StateNotifier<AuthState> {
  final AuthRepository _authRepository;

  AuthController(this._authRepository) : super(const AuthState.initial());

  Future<void> signInWithGoogle() async {
    state = const AuthState.loading();

    try {
      final response = await _authRepository.signInWithGoogle();
      state = AuthState.loggedIn(response);
    } catch (e) {
      state = AuthState.error(_getErrorMessage(e));
    }
  }

  Future<void> logout() async {
    state = const AuthState.loading();

    try {
      await _authRepository.logout();
      state = const AuthState.loggedOut();
    } catch (e) {
      state = AuthState.error(_getErrorMessage(e));
    }
  }

  Future<User?> refreshProfile() async {
    try {
      return await _authRepository.refreshUserProfile();
    } catch (e, st) {
      _log.warning('프로필 새로고침 실패', error: e, stackTrace: st);
      return null;
    }
  }

  String _getErrorMessage(dynamic error) {
    if (error is ApiException) {
      return error.message;
    }
    return '알 수 없는 오류가 발생했습니다';
  }

  void clearError() {
    if (state is AuthError) {
      state = const AuthState.initial();
    }
  }
}

// 인증 상태 클래스
sealed class AuthState {
  const AuthState();

  const factory AuthState.initial() = AuthInitial;
  const factory AuthState.loading() = AuthLoading;
  const factory AuthState.loggedIn(AuthResponse response) = AuthLoggedIn;
  const factory AuthState.loggedOut() = AuthLoggedOut;
  const factory AuthState.error(String message) = AuthError;
}

class AuthInitial extends AuthState {
  const AuthInitial();
}

class AuthLoading extends AuthState {
  const AuthLoading();
}

class AuthLoggedIn extends AuthState {
  final AuthResponse response;
  const AuthLoggedIn(this.response);
}

class AuthLoggedOut extends AuthState {
  const AuthLoggedOut();
}

class AuthError extends AuthState {
  final String message;
  const AuthError(this.message);
}
