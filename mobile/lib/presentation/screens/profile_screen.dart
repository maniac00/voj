import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';

/// 프로필 화면 — 사용자 이름 표시 및 계정 삭제
class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _deleting = false;

  @override
  Widget build(BuildContext context) {
    final userAsync = ref.watch(currentUserProvider);
    final user = userAsync.valueOrNull;
    final name = (user?.name.isNotEmpty ?? false)
        ? user!.name
        : (user?.email ?? '사용자');

    return Scaffold(
      backgroundColor: const Color(0xFFF5EDE0),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF5EDE0),
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFF3E2723)),
        title: const Text(
          '프로필',
          style: TextStyle(
            color: Color(0xFF3E2723),
            fontWeight: FontWeight.w700,
            fontSize: 20,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const SizedBox(height: 24),
              const CircleAvatar(
                radius: 40,
                backgroundColor: Color(0xFFE8DFD0),
                child: Icon(
                  Icons.person,
                  size: 48,
                  color: Color(0xFF5D4037),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                name,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Color(0xFF3E2723),
                  fontWeight: FontWeight.w700,
                  fontSize: 22,
                ),
              ),
              if (user?.email != null && user!.email != name) ...[
                const SizedBox(height: 4),
                Text(
                  user.email!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Color(0xFF5D4037),
                    fontSize: 15,
                  ),
                ),
              ],
              const Spacer(),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: _deleting ? null : _showDeleteAccountDialog,
                  style: TextButton.styleFrom(
                    foregroundColor: Colors.red.shade700,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  child: Text(_deleting ? '계정 삭제 중...' : '계정 삭제'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showDeleteAccountDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('계정 삭제'),
          content: const Text(
            '계정과 모든 이용 기록이 영구적으로 삭제되며 복구할 수 없습니다.\n\n정말로 계정을 삭제하시겠습니까?',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                _deleteAccount();
              },
              child: const Text(
                '계정 삭제',
                style: TextStyle(color: Colors.red),
              ),
            ),
          ],
        );
      },
    );
  }

  Future<void> _deleteAccount() async {
    setState(() => _deleting = true);
    await ref.read(authControllerProvider.notifier).deleteAccount();
    if (!mounted) return;

    final authState = ref.read(authControllerProvider);
    if (authState is AuthError) {
      setState(() => _deleting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('계정 삭제에 실패했습니다: ${authState.message}')),
      );
      return;
    }

    Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
  }
}
