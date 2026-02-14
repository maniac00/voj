import 'dart:async';
import 'dart:ui';

import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme/app_theme.dart';
import 'core/utils/logger.dart';
import 'presentation/screens/splash_screen.dart';
import 'presentation/screens/home_screen.dart';
import 'presentation/providers/auth_provider.dart';

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

class VoiceOfJuanApp extends StatelessWidget {
  const VoiceOfJuanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Voice of Juan',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/home': (context) => const HomeScreen(),
      },
    );
  }
}
