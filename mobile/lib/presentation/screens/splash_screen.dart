import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_config.dart';
import '../../data/models/user_model.dart';
import '../../data/services/analytics_service.dart';
import '../providers/auth_provider.dart';
import 'books_screen.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // 앱 초기화 로직 — 최소 2초 대기
    await Future.delayed(const Duration(seconds: 2));

    if (!mounted) return;

    // 자동 로그인이 꺼져 있으면 로그인 화면으로 이동
    final autoLogin = ref.read(autoLoginProvider);
    if (!autoLogin) {
      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/login');
      }
      return;
    }

    final authRepo = ref.read(authRepositoryProvider);
    // 인증 초기화(토큰 재발급 포함) 완료를 기다린 뒤 현재 상태를 확인한다.
    try {
      await authRepo.initialized.timeout(const Duration(seconds: 10));
    } catch (_) {}
    User? user = authRepo.currentUser;
    final session = authRepo.currentSession;
    if (session == null || !session.isValid) {
      user = null;
    }

    if (!mounted) return;

    // 로그인 사용자가 있으면 기기 등록 및 heartbeat 전송
    if (user != null) {
      final analytics = AnalyticsService();
      analytics.registerDevice();
      analytics.sendHeartbeat();
    }

    if (user != null && user.status == UserStatus.pending) {
      Navigator.of(context).pushReplacementNamed('/pending-approval');
    } else if (user != null && user.status == UserStatus.approved) {
      // 로그인 세션 유지 → 도서 목록으로 직접 이동
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const BooksScreen()),
      );
    } else {
      Navigator.of(context).pushReplacementNamed('/login');
    }

    if (AppConfig.authBypassEnabled && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Guest Mode: 로컬 테스트용 인증 우회 활성화'),
          backgroundColor: Colors.orange.shade700,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 배경 이미지
          Image.asset('assets/images/splash_background.png', fit: BoxFit.cover),

          // 반투명 어두운 오버레이
          Container(color: Colors.black.withValues(alpha: 0.4)),

          // 콘텐츠
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Spacer(flex: 3),

                // 앱 이름
                const Text(
                  '주안의 소리',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    letterSpacing: 1.0,
                  ),
                ),

                const SizedBox(height: 12),

                // 부제목
                const Text(
                  '시각장애인을 위한 오디오북',
                  style: TextStyle(fontSize: 18, color: Colors.white70),
                ),

                const Spacer(flex: 2),

                // 로딩 인디케이터
                const CircularProgressIndicator(
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  strokeWidth: 2.5,
                ),

                const SizedBox(height: 60),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
