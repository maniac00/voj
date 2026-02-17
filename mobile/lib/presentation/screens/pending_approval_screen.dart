import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/user_model.dart';
import '../providers/auth_provider.dart';
import 'books_screen.dart';

class PendingApprovalScreen extends ConsumerStatefulWidget {
  const PendingApprovalScreen({super.key});

  @override
  ConsumerState<PendingApprovalScreen> createState() =>
      _PendingApprovalScreenState();
}

class _PendingApprovalScreenState
    extends ConsumerState<PendingApprovalScreen> {
  bool _isChecking = false;

  Future<void> _checkApproval() async {
    setState(() => _isChecking = true);

    final user =
        await ref.read(authControllerProvider.notifier).refreshProfile();

    if (!mounted) return;

    if (user != null && user.status == UserStatus.approved) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const BooksScreen()),
        (route) => route.isFirst,
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('아직 승인 대기 중입니다'),
          duration: Duration(seconds: 2),
        ),
      );
    }

    if (mounted) {
      setState(() => _isChecking = false);
    }
  }

  Future<void> _logout() async {
    await ref.read(authControllerProvider.notifier).logout();
    if (mounted) {
      Navigator.of(context).pushReplacementNamed('/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),

              // 대기 아이콘
              Icon(
                Icons.hourglass_empty,
                size: 80,
                color: Colors.orange.shade600,
                semanticLabel: '승인 대기 중',
              ),

              const SizedBox(height: 24),

              Text(
                '승인 대기 중',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Colors.orange.shade700,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 16),

              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.orange.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.orange.shade200),
                ),
                child: Text(
                  '회원 가입이 완료되었습니다.\n'
                  '관리자의 승인을 기다려주세요.\n'
                  '1영업일 이내에 승인해드립니다.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Colors.orange.shade800,
                    height: 1.5,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),

              const SizedBox(height: 32),

              // 확인 버튼
              ElevatedButton(
                onPressed: _isChecking ? null : _checkApproval,
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 56),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isChecking
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('확인'),
              ),

              const SizedBox(height: 12),

              // 로그아웃 버튼
              TextButton.icon(
                onPressed: _logout,
                icon: const Icon(Icons.logout, size: 20),
                label: const Text('로그아웃'),
              ),

              const Spacer(),
            ],
          ),
        ),
      ),
    );
  }
}
