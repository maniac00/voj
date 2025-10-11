import 'dart:async';
import 'dart:ui' as ui;

import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';

class AccessibilityFeedbackService {
  const AccessibilityFeedbackService({this.textDirection = ui.TextDirection.ltr});

  final ui.TextDirection textDirection;

  Future<void> announce(String message, {bool withHaptic = false}) async {
    if (message.isEmpty) {
      return;
    }

    try {
      await SemanticsService.announce(message, textDirection);
    } catch (_) {
      // SemanticsService가 초기화되지 않은 경우 무시
    }

    if (withHaptic) {
      await _safeHaptic(HapticFeedback.selectionClick);
    }
  }

  Future<void> warn(String message) async {
    await announce(message, withHaptic: true);
  }

  Future<void> error(String message) async {
    await announce(message, withHaptic: true);
    await _safeHaptic(HapticFeedback.heavyImpact);
  }

  Future<void> success(String message) async {
    await announce(message, withHaptic: true);
    await _safeHaptic(HapticFeedback.lightImpact);
  }

  Future<void> _safeHaptic(Future<void> Function() callback) async {
    try {
      await callback();
    } catch (_) {
      // 일부 플랫폼에서는 햅틱을 지원하지 않으므로 무시
    }
  }
}
