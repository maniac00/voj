import 'package:flutter/material.dart';

/// 앱 전역 색상 팔레트
///
/// 화면마다 하드코딩되어 있던 크림/브라운 색을 한곳으로 모은 것.
/// 다이얼로그·팝업 메뉴·스낵바는 ThemeData를 따르므로, 테마가 이 팔레트를
/// 쓰지 않으면 화면과 팝업의 색이 어긋난다.
class AppColors {
  /// 화면 기본 배경 (크림)
  static const background = Color(0xFFF5EDE0);

  /// 카드·다이얼로그 표면 (거의 흰색에 가까운 크림)
  static const surface = Color(0xFFFFFDF8);

  /// 입력 필드 배경 — 다이얼로그 표면과 반드시 구분되어야 함
  /// (surface 대비 1.35:1, 본문 텍스트 대비 10.1:1)
  static const fieldFill = Color(0xFFE8DACA);

  /// 주요 액션 색 (브라운)
  static const primary = Color(0xFF5D4037);

  /// 본문 텍스트
  static const textPrimary = Color(0xFF3E2723);

  /// 보조 텍스트
  static const textSecondary = Color(0xFF6D4C41);

  /// 테두리·구분선
  static const outline = Color(0xFF8D6E63);

  /// 검색 상태 바 배경
  static const bannerBackground = Color(0xFFE8DFD0);
}

class AppTheme {
  static ThemeData buildTheme() {
    final scheme =
        ColorScheme.fromSeed(
          seedColor: AppColors.primary,
          brightness: Brightness.light,
        ).copyWith(
          primary: AppColors.primary,
          onPrimary: Colors.white,
          surface: AppColors.surface,
          onSurface: AppColors.textPrimary,
          onSurfaceVariant: AppColors.textSecondary,
          // AlertDialog·PopupMenu의 M3 기본 배경이 참조하는 토큰
          surfaceContainerHigh: AppColors.surface,
          // 입력 필드 배경이 참조하는 토큰 (다이얼로그 표면과 다른 색)
          surfaceContainerHighest: AppColors.fieldFill,
          outline: AppColors.outline,
        );

    const textTheme = TextTheme(
      displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
      displayMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.w600),
      titleLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
      titleMedium: TextStyle(fontSize: 20, fontWeight: FontWeight.w500),
      bodyLarge: TextStyle(fontSize: 18),
      bodyMedium: TextStyle(fontSize: 16),
      labelLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: scheme,
      primaryColor: scheme.primary, // 하위 호환
      scaffoldBackgroundColor: AppColors.background,
      textTheme: textTheme,

      // 다이얼로그 — 앱 팔레트로 고정 (시스템 다크모드에 끌려가지 않도록)
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 6,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        titleTextStyle: const TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: AppColors.textPrimary,
        ),
        contentTextStyle: const TextStyle(
          fontSize: 17,
          height: 1.4,
          color: AppColors.textPrimary,
        ),
      ),

      // 팝업 메뉴 (프로필 메뉴)
      popupMenuTheme: PopupMenuThemeData(
        color: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        elevation: 6,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w500,
          color: AppColors.textPrimary,
        ),
      ),

      // 스낵바 — 기본 테마는 반전색을 쓰므로 명시
      snackBarTheme: const SnackBarThemeData(
        backgroundColor: AppColors.textPrimary,
        contentTextStyle: TextStyle(fontSize: 16, color: Colors.white),
        actionTextColor: Color(0xFFD7CCC8),
        behavior: SnackBarBehavior.floating,
      ),

      // 바텀시트
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.background,
        surfaceTintColor: Colors.transparent,
      ),

      // 다이얼로그 액션 버튼 — 크림 배경에서 읽히는 색으로 고정하고,
      // M3 기본 최소 높이(40dp)를 Android 접근성 기준인 48dp로 올린다.
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: AppColors.primary,
          textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          minimumSize: const Size(64, 48),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          minimumSize: const Size(200, 60),
          textStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.fieldFill,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(width: 2, color: AppColors.outline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(width: 2, color: AppColors.outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(width: 3, color: AppColors.primary),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(width: 2, color: scheme.error),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(width: 3, color: scheme.error),
        ),
        contentPadding: const EdgeInsets.all(20),
      ),

      visualDensity: VisualDensity.adaptivePlatformDensity,
    );
  }

  static final ThemeData lightTheme = buildTheme();
}
