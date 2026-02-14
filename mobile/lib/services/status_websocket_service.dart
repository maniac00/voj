import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../core/constants/app_config.dart';
import '../core/utils/logger.dart';

const _log = AppLogger('StatusWebSocket');

class StatusWebSocketService {
  StatusWebSocketService(
    this.chapterId, {
    this.retryBaseDelay = const Duration(seconds: 2),
  }) : _uri = AppConfig.wsUri('/ws/status/$chapterId');

  final String chapterId;
  final Uri _uri;
  final Duration retryBaseDelay;

  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  bool _isClosed = false;
  int _retryAttempt = 0;

  final _controller = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get stream => _controller.stream;

  Future<void> connect() async {
    if (_channel != null) return;
    await _openChannel();
  }

  void send(Map<String, dynamic> payload) {
    _channel?.sink.add(json.encode(payload));
  }

  Future<void> _openChannel() async {
    try {
      _channel = WebSocketChannel.connect(_uri);
      _isClosed = false;
      _retryAttempt = 0;

      _subscription = _channel!.stream.listen(
        (event) {
          if (event is String) {
            final decoded = json.decode(event);
            if (decoded is Map<String, dynamic>) {
              _controller.add(decoded);
            }
          }
        },
        onError: (e) {
          _log.warning('WebSocket 스트림 오류', error: e);
          _scheduleReconnect();
        },
        onDone: _scheduleReconnect,
      );

      send({'type': 'subscribe', 'chapter_id': chapterId});
    } catch (e, st) {
      _log.warning('WebSocket 연결 실패', error: e, stackTrace: st);
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect([dynamic _]) {
    if (_isClosed) return;
    _subscription?.cancel();
    _subscription = null;
    _channel = null;

    final delay = retryBaseDelay * (_retryAttempt + 1);
    _retryAttempt += 1;
    Future.delayed(delay, () {
      if (_isClosed) return;
      _openChannel();
    });
  }

  Future<void> dispose() async {
    _isClosed = true;
    try {
      send({'type': 'unsubscribe', 'chapter_id': chapterId});
    } catch (_) {}
    await _subscription?.cancel();
    await _controller.close();
    _channel?.sink.close();
  }
}

