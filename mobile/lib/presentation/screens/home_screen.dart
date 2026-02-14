import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';
import '../../data/models/user_model.dart';
import 'login_screen.dart';
import 'books_screen.dart';
import '../../core/constants/app_config.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync = ref.watch(currentUserProvider);
    final isLoggedIn = ref.watch(isLoggedInProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Voice of Juan'),
            if (AppConfig.authBypassEnabled) ...[
              const SizedBox(width: 8),
              const _GuestBadge(),
            ],
          ],
        ),
        centerTitle: true,
        actions: [
          if (isLoggedIn)
            IconButton(
              onPressed: () => _showLogoutDialog(context, ref),
              icon: const Icon(Icons.logout),
              tooltip: '로그아웃',
            ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 상단 로고 영역
              Container(
                alignment: Alignment.center,
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Icon(
                      Icons.headphones,
                      size: 80,
                      color: Theme.of(context).colorScheme.primary,
                      semanticLabel: 'Voice of Juan 로고',
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Voice of Juan',
                      style: Theme.of(context).textTheme.headlineLarge
                          ?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '시각장애인을 위한 오디오북',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 40),

              // 사용자 상태에 따른 콘텐츠
              Expanded(
                child: userAsync.when(
                  data: (user) {
                    if (user == null) {
                      return _buildLoggedOutContent(context, ref);
                    }
                    if (user.status == UserStatus.pending) {
                      return _buildPendingContent(context, ref, user);
                    }
                    if (user.status == UserStatus.suspended) {
                      return _buildSuspendedContent(context, ref);
                    }
                    return _buildApprovedContent(context, user);
                  },
                  loading: () =>
                      const Center(child: CircularProgressIndicator()),
                  error: (error, stack) => _buildErrorContent(context, error),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPendingContent(BuildContext context, WidgetRef ref, User user) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
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
            '회원가입이 완료되었습니다.\n\n'
            '관리자가 인증하기 전입니다.\n'
            '1 영업일 이내에 승인해드립니다.\n\n'
            '승인 후 오디오북 서비스를 이용하실 수 있습니다.',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Colors.orange.shade800,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
        ),

        const SizedBox(height: 32),

        // 승인 확인 버튼
        OutlinedButton.icon(
          onPressed: () {
            ref.read(authControllerProvider.notifier).refreshProfile();
          },
          icon: const Icon(Icons.refresh),
          label: const Text('승인 확인'),
          style: OutlinedButton.styleFrom(
            minimumSize: const Size(double.infinity, 56),
            side: BorderSide(color: Colors.orange.shade400),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),

        const SizedBox(height: 12),

        // 로그아웃 버튼
        TextButton.icon(
          onPressed: () => _showLogoutDialog(context, ref),
          icon: const Icon(Icons.logout, size: 20),
          label: const Text('로그아웃'),
        ),

        const Spacer(),
      ],
    );
  }

  Widget _buildSuspendedContent(BuildContext context, WidgetRef ref) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Spacer(),

        Icon(
          Icons.block,
          size: 80,
          color: Colors.red.shade600,
          semanticLabel: '계정 정지됨',
        ),

        const SizedBox(height: 24),

        Text(
          '계정이 정지되었습니다',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
            color: Colors.red.shade700,
          ),
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 16),

        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.red.shade50,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.red.shade200),
          ),
          child: Text(
            '자세한 내용은 관리자에게 문의해주세요.',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Colors.red.shade800,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
        ),

        const SizedBox(height: 32),

        TextButton.icon(
          onPressed: () => _showLogoutDialog(context, ref),
          icon: const Icon(Icons.logout, size: 20),
          label: const Text('로그아웃'),
        ),

        const Spacer(),
      ],
    );
  }

  Widget _buildApprovedContent(BuildContext context, User user) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 환영 메시지
        Text(
          '${user.name.isNotEmpty ? user.name : '사용자'}님, 환영합니다!',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 32),

        // 오디오북 둘러보기 버튼
        ElevatedButton.icon(
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const BooksScreen()),
            );
          },
          icon: const Icon(Icons.library_books),
          label: const Text('오디오북 둘러보기'),
          style: ElevatedButton.styleFrom(
            minimumSize: const Size(double.infinity, 60),
          ),
        ),
      ],
    );
  }

  Widget _buildLoggedOutContent(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // 안내 메시지
        Container(
          padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Icon(
                Icons.info_outline,
                size: 48,
                  color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 16),
              Text(
                '로그인이 필요합니다',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.primary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Voice of Juan의 오디오북 서비스를 이용하려면 로그인해주세요.',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),

        const Spacer(),

        // 로그인 버튼
        ElevatedButton.icon(
          onPressed: () async {
            final result = await Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const LoginScreen()),
            );

            // 로그인 성공 시 사용자 프로필 새로고침
            if (result == true) {
              ref.read(authControllerProvider.notifier).refreshProfile();
            }
          },
          icon: const Icon(Icons.login),
          label: const Text('로그인'),
          style: ElevatedButton.styleFrom(
            minimumSize: const Size(double.infinity, 60),
          ),
        ),
      ],
    );
  }

  Widget _buildErrorContent(BuildContext context, Object error) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.error_outline, size: 48, color: Colors.red),
        const SizedBox(height: 16),
        Text(
          '오류가 발생했습니다',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            color: Colors.red,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          error.toString(),
          style: Theme.of(context).textTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('로그아웃'),
          content: const Text('정말로 로그아웃하시겠습니까?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                ref.read(authControllerProvider.notifier).logout();
              },
              child: const Text('로그아웃'),
            ),
          ],
        );
      },
    );
  }
}

class _GuestBadge extends StatelessWidget {
  const _GuestBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.orange.shade600,
        borderRadius: BorderRadius.circular(6),
      ),
      child: const Text(
        'Guest Mode',
        style: TextStyle(
          fontSize: 12,
          color: Colors.white,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
