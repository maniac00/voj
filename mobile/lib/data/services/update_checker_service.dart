import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../core/utils/logger.dart';

const _log = AppLogger('UpdateChecker');

/// 앱 업데이트 확인 서비스
/// Cloudflare R2에 호스팅된 metadata.json과 현재 앱 버전을 비교
class UpdateCheckerService {
  final String _metadataUrl;
  final String _currentVersion;

  UpdateCheckerService({
    required String metadataUrl,
    required String currentVersion,
  })  : _metadataUrl = metadataUrl,
        _currentVersion = currentVersion;

  /// 업데이트 확인 후 새 버전이 있으면 정보 반환
  Future<UpdateInfo?> checkForUpdate() async {
    try {
      final response = await http.get(Uri.parse(_metadataUrl));
      if (response.statusCode != 200) {
        _log.warning('Failed to fetch metadata: ${response.statusCode}');
        return null;
      }

      final data = json.decode(response.body) as Map<String, dynamic>;
      final android = data['android'] as Map<String, dynamic>?;
      if (android == null) return null;

      final latestVersion = android['latestVersion'] as String? ?? '';
      final downloadUrl = android['downloadUrl'] as String? ?? '';
      final changelog = android['changelog'] as String? ?? '';

      if (latestVersion.isEmpty || downloadUrl.isEmpty) return null;
      if (!_isNewerVersion(latestVersion, _currentVersion)) return null;

      return UpdateInfo(
        latestVersion: latestVersion,
        downloadUrl: downloadUrl,
        changelog: changelog,
      );
    } catch (e) {
      _log.warning('Update check error', error: e);
      return null;
    }
  }

  /// 시맨틱 버전 비교: latest > current이면 true
  bool _isNewerVersion(String latest, String current) {
    final latestParts = latest.split('.').map((s) => int.tryParse(s) ?? 0).toList();
    final currentParts = current.split('.').map((s) => int.tryParse(s) ?? 0).toList();

    for (var i = 0; i < 3; i++) {
      final l = i < latestParts.length ? latestParts[i] : 0;
      final c = i < currentParts.length ? currentParts[i] : 0;
      if (l > c) return true;
      if (l < c) return false;
    }
    return false;
  }

  /// 업데이트 안내 다이얼로그 표시
  static void showUpdateDialog(BuildContext context, UpdateInfo info) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('새 버전이 있습니다'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('최신 버전: ${info.latestVersion}'),
            if (info.changelog.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(info.changelog),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('나중에'),
          ),
        ],
        semanticLabel: '앱 업데이트 안내',
      ),
    );
  }
}

class UpdateInfo {
  final String latestVersion;
  final String downloadUrl;
  final String changelog;

  const UpdateInfo({
    required this.latestVersion,
    required this.downloadUrl,
    required this.changelog,
  });
}
