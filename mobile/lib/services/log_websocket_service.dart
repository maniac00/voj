import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';
import '../core/constants/app_config.dart';

class LogWebSocketService {
  LogWebSocketService({this.retryBaseDelay = const Duration(seconds: 2)})
      : _uri = AppConfig.wsUri('/ws/logs');

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
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
      );

      send({'type': 'subscribe'});
    } catch (_) {
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
      send({'type': 'unsubscribe'});
    } catch (_) {}
    await _subscription?.cancel();
    await _controller.close();
    _channel?.sink.close();
  }
}

