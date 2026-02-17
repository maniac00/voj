import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class SavedPlaybackState {
  final String chapterId;
  final int chapterNumber;
  final String chapterFileName;
  final int positionSeconds;

  const SavedPlaybackState({
    required this.chapterId,
    required this.chapterNumber,
    required this.chapterFileName,
    required this.positionSeconds,
  });

  String get resumeLabel {
    final minutes = positionSeconds ~/ 60;
    final seconds = positionSeconds % 60;
    final mm = minutes.toString().padLeft(2, '0');
    final ss = seconds.toString().padLeft(2, '0');
    return '챕터$chapterNumber $mm분 $ss초부터 다시 시작';
  }

  Map<String, dynamic> toJson() => {
        'chapterId': chapterId,
        'chapterNumber': chapterNumber,
        'chapterFileName': chapterFileName,
        'positionSeconds': positionSeconds,
      };

  factory SavedPlaybackState.fromJson(Map<String, dynamic> json) {
    return SavedPlaybackState(
      chapterId: json['chapterId'] as String,
      chapterNumber: json['chapterNumber'] as int,
      chapterFileName: json['chapterFileName'] as String,
      positionSeconds: json['positionSeconds'] as int,
    );
  }
}

class LocalPlaybackState {
  static String _key(String bookId) => 'last_playback_$bookId';

  static Future<void> save(
    SharedPreferences prefs, {
    required String bookId,
    required String chapterId,
    required int chapterNumber,
    required String chapterFileName,
    required int positionSeconds,
  }) async {
    final state = SavedPlaybackState(
      chapterId: chapterId,
      chapterNumber: chapterNumber,
      chapterFileName: chapterFileName,
      positionSeconds: positionSeconds,
    );
    await prefs.setString(_key(bookId), jsonEncode(state.toJson()));
  }

  static SavedPlaybackState? load(SharedPreferences prefs, String bookId) {
    final raw = prefs.getString(_key(bookId));
    if (raw == null) return null;
    try {
      return SavedPlaybackState.fromJson(
        jsonDecode(raw) as Map<String, dynamic>,
      );
    } catch (_) {
      return null;
    }
  }

  static Future<void> clear(SharedPreferences prefs, String bookId) async {
    await prefs.remove(_key(bookId));
  }
}
