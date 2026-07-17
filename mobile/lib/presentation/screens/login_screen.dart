import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:package_info_plus/package_info_plus.dart';
import '../../data/models/user_model.dart';
import '../providers/auth_provider.dart';
import 'books_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  static final bool _supportsAppleSignIn = !kIsWeb && Platform.isIOS;

  String _appVersion = '';

  @override
  void initState() {
    super.initState();
    PackageInfo.fromPlatform().then((info) {
      if (mounted) setState(() => _appVersion = 'v${info.version}');
    });
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    ref.listen<AuthState>(authControllerProvider, (previous, next) {
      if (next is AuthLoggedIn) {
        final user = next.response.user;
        final isNew = next.response.message == 'new_user';

        if (user != null && user.status == UserStatus.pending) {
          if (isNew) {
            _showRegistrationSuccessDialog();
          } else {
            Navigator.of(context).pushNamedAndRemoveUntil(
              '/pending-approval',
              (route) => false,
            );
          }
        } else {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (context) => const BooksScreen()),
            (route) => route.isFirst,
          );
        }
      } else if (next is AuthError) {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('로그인 오류'),
            content: SelectableText(next.message),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('확인'),
              ),
            ],
          ),
        );
      }
    });

    return Scaffold(
      backgroundColor: const Color(0xFFF5EDE0),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF5EDE0),
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.arrow_back, color: Color(0xFF3E2723)),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),

              // 앱 이름
              const Text(
                '주안의 소리',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF3E2723),
                  letterSpacing: 0.5,
                  fontFamily: 'serif',
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 8),

              // 부제목
              const Text(
                '시각장애인을 위한 오디오북',
                style: TextStyle(
                  fontSize: 16,
                  color: Color(0xFF8D7B68),
                  fontWeight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 48),

              // Google 로그인 버튼
              Semantics(
                label: 'Google 계정으로 로그인. 탭하면 Google 로그인 화면으로 이동합니다.',
                button: true,
                child: SizedBox(
                  height: 64,
                  child: ElevatedButton(
                    onPressed: authState is AuthLoading
                        ? null
                        : () {
                            ref
                                .read(authControllerProvider.notifier)
                                .signInWithGoogle();
                          },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: const Color(0xFF3E2723),
                      disabledBackgroundColor: Colors.grey[200],
                      elevation: 2,
                      shadowColor: Colors.black.withValues(alpha: 0.15),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: const BorderSide(
                          color: Color(0xFFD0C4B0),
                          width: 1.5,
                        ),
                      ),
                    ),
                    child: authState is AuthLoading
                        ? const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2.5,
                                  color: Color(0xFF5D4037),
                                ),
                              ),
                              SizedBox(width: 12),
                              Text(
                                '로그인 중...',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          )
                        : Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              _buildGoogleLogo(),
                              const SizedBox(width: 12),
                              const Text(
                                'Google로 로그인',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                  ),
                ),
              ),

              // Apple 로그인 버튼 (iOS 전용 — App Store 가이드라인 4.8)
              if (_supportsAppleSignIn) ...[
                const SizedBox(height: 16),
                Semantics(
                  label: 'Apple 계정으로 로그인. 탭하면 Apple 로그인 화면으로 이동합니다.',
                  button: true,
                  child: SizedBox(
                    height: 64,
                    child: ElevatedButton(
                      onPressed: authState is AuthLoading
                          ? null
                          : () {
                              ref
                                  .read(authControllerProvider.notifier)
                                  .signInWithApple();
                            },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.black,
                        foregroundColor: Colors.white,
                        disabledBackgroundColor: Colors.grey[400],
                        elevation: 2,
                        shadowColor: Colors.black.withValues(alpha: 0.15),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.apple, size: 28, color: Colors.white),
                          SizedBox(width: 12),
                          Text(
                            'Apple로 로그인',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],

              const SizedBox(height: 16),

              // 로그인 없이 둘러보기 (App Store 5.1.1(v) — 비계정 기능 접근)
              Semantics(
                label: '로그인 없이 둘러보기. 로그인하지 않고 공개 오디오북을 들을 수 있습니다.',
                button: true,
                child: SizedBox(
                  height: 56,
                  child: OutlinedButton(
                    onPressed: authState is AuthLoading
                        ? null
                        : () async {
                            await ref
                                .read(authRepositoryProvider)
                                .enterGuestMode();
                            if (!context.mounted) return;
                            Navigator.of(context).pushReplacement(
                              MaterialPageRoute(
                                builder: (context) => const BooksScreen(),
                              ),
                            );
                          },
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF5D4037),
                      side: const BorderSide(color: Color(0xFF5D4037)),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: const Text(
                      '로그인 없이 둘러보기',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 12),

              // 자동 로그인 체크박스
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 24,
                    height: 24,
                    child: Checkbox(
                      value: ref.watch(autoLoginProvider),
                      activeColor: const Color(0xFF5D4037),
                      onChanged: (value) {
                        final prefs = ref.read(sharedPreferencesProvider);
                        prefs.setBool('auto_login', value ?? true);
                        ref.invalidate(autoLoginProvider);
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    '자동 로그인',
                    style: TextStyle(
                      fontSize: 14,
                      color: Color(0xFF5D4037),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 48),

              // 버전 표시 (pubspec.yaml에서 자동 읽기)
              Text(
                _appVersion,
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFFAA9B8C),
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGoogleLogo() {
    return SizedBox(
      width: 24,
      height: 24,
      child: CustomPaint(
        painter: _GoogleLogoPainter(),
      ),
    );
  }

  void _showRegistrationSuccessDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          backgroundColor: const Color(0xFFFFFDF8),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          icon: const Icon(
            Icons.check_circle,
            color: Color(0xFF4CAF50),
            size: 56,
          ),
          title: const Text(
            '회원가입 완료',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Color(0xFF3E2723),
              fontWeight: FontWeight.w700,
            ),
          ),
          content: const Text(
            '회원가입이 성공적으로 완료되었습니다!\n\n'
            '관리자가 회원 정보를 확인한 후\n'
            '승인해드립니다.\n'
            '1영업일 이내에 처리됩니다.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Color(0xFF5D4037),
              height: 1.5,
            ),
          ),
          actions: [
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(dialogContext).pop();
                  Navigator.of(context).pushNamedAndRemoveUntil(
                    '/pending-approval',
                    (route) => false,
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF5D4037),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  minimumSize: const Size(double.infinity, 48),
                ),
                child: const Text(
                  '확인',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

/// Google 로고를 CustomPaint로 그리기 (네트워크 의존 없음)
class _GoogleLogoPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final double w = size.width;
    final double h = size.height;
    final double cx = w / 2;
    final double cy = h / 2;
    final double r = w * 0.45;

    // 파란색 (우상단)
    final bluePaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.18
      ..strokeCap = StrokeCap.butt;
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      -0.9, // ~-50 deg
      1.5, // ~85 deg
      false,
      bluePaint,
    );

    // 초록색 (우하단)
    final greenPaint = Paint()
      ..color = const Color(0xFF34A853)
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.18
      ..strokeCap = StrokeCap.butt;
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      0.6,
      1.0,
      false,
      greenPaint,
    );

    // 노란색 (좌하단)
    final yellowPaint = Paint()
      ..color = const Color(0xFFFBBC05)
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.18
      ..strokeCap = StrokeCap.butt;
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      1.6,
      1.0,
      false,
      yellowPaint,
    );

    // 빨간색 (좌상단)
    final redPaint = Paint()
      ..color = const Color(0xFFEA4335)
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.18
      ..strokeCap = StrokeCap.butt;
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      2.6,
      1.0,
      false,
      redPaint,
    );

    // 가운데 가로 막대 (파란색)
    final barPaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.fill;
    canvas.drawRect(
      Rect.fromLTWH(cx - w * 0.02, cy - h * 0.09, w * 0.48, h * 0.18),
      barPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
