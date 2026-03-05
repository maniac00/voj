import 'dart:async';
import 'dart:ui';

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio_background/just_audio_background.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/navigation/app_route_observer.dart';
import 'core/theme/app_theme.dart';
import 'core/utils/logger.dart';
import 'presentation/screens/splash_screen.dart';
import 'presentation/screens/login_screen.dart';
import 'presentation/screens/pending_approval_screen.dart';
import 'presentation/providers/auth_provider.dart';
import 'presentation/providers/audio_player_provider.dart';

const _log = AppLogger('Main');

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Flutter 프레임워크 에러 핸들링
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    _log.severe(
      'Flutter error: ${details.exceptionAsString()}',
      error: details.exception,
      stackTrace: details.stack,
    );
  };

  // 플랫폼 디스패처 에러 핸들링
  PlatformDispatcher.instance.onError = (error, stack) {
    _log.severe('Platform error', error: error, stackTrace: stack);
    return true;
  };

  // 오디오 백그라운드 서비스 초기화 (foreground service + 알림바 미디어 컨트롤)
  await JustAudioBackground.init(
    androidNotificationChannelId: 'com.voiceofjuan.audio',
    androidNotificationChannelName: '주안의 소리',
    androidNotificationOngoing: true,
  );

  // Firebase 초기화
  await Firebase.initializeApp();

  // SharedPreferences 초기화
  final sharedPreferences = await SharedPreferences.getInstance();

  runZonedGuarded(
    () {
      runApp(
        ProviderScope(
          overrides: [
            sharedPreferencesProvider.overrideWithValue(sharedPreferences),
          ],
          child: const VoiceOfJuanApp(),
        ),
      );
    },
    (error, stack) {
      _log.severe('Unhandled zone error', error: error, stackTrace: stack);
    },
  );
}

final _navigatorKey = GlobalKey<NavigatorState>();

class VoiceOfJuanApp extends ConsumerStatefulWidget {
  const VoiceOfJuanApp({super.key});

  @override
  ConsumerState<VoiceOfJuanApp> createState() => _VoiceOfJuanAppState();
}

class _VoiceOfJuanAppState extends ConsumerState<VoiceOfJuanApp>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      ref.read(audioPlayerServiceProvider).saveProgressLocally();
    }
  }

  @override
  Widget build(BuildContext context) {
    // 로그인 상태가 true → false로 전환되면 로그인 화면으로 이동
    // (토큰 만료, 세션 강제 해제 등 모든 로그아웃 경로 처리)
    ref.listen<bool>(isLoggedInProvider, (previous, next) {
      if (previous == true && !next) {
        _log.info('세션 만료 감지 — 로그인 화면으로 이동');
        _navigatorKey.currentState?.pushNamedAndRemoveUntil(
          '/login',
          (route) => false,
        );
      }
    });

    return MaterialApp(
      navigatorKey: _navigatorKey,
      navigatorObservers: [appRouteObserver],
      title: '주안의 소리',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/login': (context) => const LoginScreen(),
        '/pending-approval': (context) => const PendingApprovalScreen(),
      },
    );
  }
}
