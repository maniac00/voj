import 'dart:developer' as developer;

/// 앱 전역 로거 유틸리티
/// dart:developer.log 기반으로 구조화된 로깅을 제공합니다.
class AppLogger {
  final String name;

  const AppLogger(this.name);

  void debug(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: name,
      level: 500,
      error: error,
      stackTrace: stackTrace,
    );
  }

  void info(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: name,
      level: 800,
      error: error,
      stackTrace: stackTrace,
    );
  }

  void warning(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: name,
      level: 900,
      error: error,
      stackTrace: stackTrace,
    );
  }

  void severe(String message, {Object? error, StackTrace? stackTrace}) {
    developer.log(
      message,
      name: name,
      level: 1000,
      error: error,
      stackTrace: stackTrace,
    );
  }
}
