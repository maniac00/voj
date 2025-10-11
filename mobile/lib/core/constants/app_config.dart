class AppConfig {
  static const String _defaultApiBaseUrl = 'http://localhost:8080/api/v1';

  static const String apiBaseUrl = String.fromEnvironment(
    'VOJ_API_BASE_URL',
    defaultValue: _defaultApiBaseUrl,
  );

  // Guest Mode(인증 우회) 플래그 - 기본 비활성
  static const bool authBypassEnabled = bool.fromEnvironment(
    'VOJ_AUTH_BYPASS',
    defaultValue: false,
  );

  static Uri apiUri(String path) {
    final base = apiBaseUrl.endsWith('/')
        ? apiBaseUrl.substring(0, apiBaseUrl.length - 1)
        : apiBaseUrl;
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$base$normalizedPath');
  }

  static Uri wsUri(String path) {
    final base = Uri.parse(apiBaseUrl);
    final scheme = base.scheme == 'https' ? 'wss' : 'ws';
    final authority = base.hasPort ? '${base.host}:${base.port}' : base.host;
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    // API_BASE가 '/api/v1' 같은 path를 포함하므로, 그 뒤에 WS 경로를 붙여야 함
    final basePath = base.path.endsWith('/') ? base.path.substring(0, base.path.length - 1) : base.path;
    final combinedPath = '$basePath$normalizedPath';
    return Uri.parse('$scheme://$authority$combinedPath');
  }
}
