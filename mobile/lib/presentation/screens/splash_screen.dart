import 'package:flutter/material.dart';
import '../../core/constants/app_config.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // 앱 초기화 로직
    await Future.delayed(const Duration(seconds: 2));
    
    if (mounted) {
      // Guest Mode에서는 로그인 패스(현재도 홈으로 이동)
      Navigator.of(context).pushReplacementNamed('/home');
      if (AppConfig.authBypassEnabled) {
        // 게스트 모드 안내 토스트
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Guest Mode: 로컬 테스트용 인증 우회 활성화'),
            backgroundColor: Colors.orange.shade700,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).primaryColor,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 앱 로고 (추후 이미지로 교체)
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Icon(
                Icons.headphones,
                size: 60,
                color: Theme.of(context).primaryColor,
              ),
            ),
            
            const SizedBox(height: 40),
            
            // 앱 이름
            const Text(
              'Voice of Juan',
              style: TextStyle(
                fontSize: 36,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            
            const SizedBox(height: 16),
            
            // 부제목
            const Text(
              '시각장애인을 위한 오디오북',
              style: TextStyle(
                fontSize: 18,
                color: Colors.white70,
              ),
            ),
            
            const SizedBox(height: 60),
            
            // 로딩 인디케이터
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ],
        ),
      ),
    );
  }
}