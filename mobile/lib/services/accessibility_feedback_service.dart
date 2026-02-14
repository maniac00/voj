import 'dart:async';
import 'dart:ui' as ui;

import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import '../core/utils/logger.dart';

const _log = AppLogger('Accessibility');

class AccessibilityFeedbackService {
  const AccessibilityFeedbackService({this.textDirection = ui.TextDirection.ltr});

  final ui.TextDirection textDirection;

  Future<void> announce(String message, {bool withHaptic = false}) async {
    if (message.isEmpty) {
      return;
    }

    try {
      await SemanticsService.announce(message, textDirection);
    } catch (e) {
      _log.debug('SemanticsService 초기화 안됨', error: e);
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
    } catch (e) {
      _log.debug('햅틱 피드백 미지원 플랫폼', error: e);
    }
  }
}
