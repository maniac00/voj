import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/user_model.dart';
import '../providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    ref.listen<AuthState>(authControllerProvider, (previous, next) {
      if (next is AuthLoggedIn) {
        final user = next.response.user;
        final isNew = next.response.message == 'new_user';

        if (isNew && user != null && user.status == UserStatus.pending) {
          // 신규 가입 → 가입 성공 다이얼로그 표시 후 홈으로
          _showRegistrationSuccessDialog();
        } else {
          // 기존 사용자 → 바로 홈으로
          Navigator.of(context).pop(true);
        }
      } else if (next is AuthError) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    });

    return Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        title: const Text('로그인'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 48),

              Text(
                'Voice of Juan',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 8),

              Text(
                '시각장애인을 위한 오디오북',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),

              const Spacer(),

              // Google 로그인 버튼
              SizedBox(
                height: 56,
                child: OutlinedButton.icon(
                  onPressed: authState is AuthLoading
                      ? null
                      : () {
                          ref
                              .read(authControllerProvider.notifier)
                              .signInWithGoogle();
                        },
                  icon: authState is AuthLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Image.network(
                          'https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg',
                          width: 24,
                          height: 24,
                          errorBuilder: (context, error, stackTrace) =>
                              const Icon(Icons.login, size: 24),
                        ),
                  label: Text(
                    authState is AuthLoading ? '로그인 중...' : 'Google로 로그인',
                    style: const TextStyle(fontSize: 16),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.grey),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 24),

              Text(
                '처음 로그인하면 자동으로 회원가입됩니다.\n관리자 승인 후 서비스를 이용하실 수 있습니다.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey[500],
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 48),
            ],
          ),
        ),
      ),
    );
  }

  void _showRegistrationSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          icon: Icon(
            Icons.check_circle,
            color: Colors.green,
            size: 48,
          ),
          title: const Text(
            '회원가입 완료',
            textAlign: TextAlign.center,
          ),
          content: const Text(
            '회원가입이 성공적으로 완료되었습니다!\n\n'
            '관리자가 인증하기 전입니다.\n'
            '1 영업일 이내에 승인해드립니다.',
            textAlign: TextAlign.center,
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop(); // 다이얼로그 닫기
                Navigator.of(context).pop(true); // LoginScreen 닫기 → HomeScreen
              },
              child: const Text('확인'),
            ),
          ],
        );
      },
    );
  }
}
