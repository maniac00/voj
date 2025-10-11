import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/audio_player_provider.dart';
import '../widgets/audio_player_widget.dart';
import '../screens/audio_player_screen.dart';

/// 앱 전역에서 사용하는 스캐폴드 래퍼
/// 미니 플레이어를 포함하여 모든 화면에서 오디오 재생 제어가 가능하도록 함
class AppScaffold extends ConsumerWidget {
  final PreferredSizeWidget? appBar;
  final Widget body;
  final Widget? floatingActionButton;
  final Widget? bottomNavigationBar;
  final Widget? drawer;
  final Widget? endDrawer;
  final Color? backgroundColor;
  final bool extendBodyBehindAppBar;
  final bool extendBody;

  const AppScaffold({
    super.key,
    this.appBar,
    required this.body,
    this.floatingActionButton,
    this.bottomNavigationBar,
    this.drawer,
    this.endDrawer,
    this.backgroundColor,
    this.extendBodyBehindAppBar = false,
    this.extendBody = false,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final showMiniPlayer = ref.watch(showMiniPlayerProvider);

    return Scaffold(
      appBar: appBar,
      backgroundColor: backgroundColor,
      extendBodyBehindAppBar: extendBodyBehindAppBar,
      extendBody: extendBody,
      drawer: drawer,
      endDrawer: endDrawer,
      floatingActionButton: floatingActionButton,
      body: Stack(
        children: [
          // 메인 콘텐츠
          Positioned.fill(
            bottom: showMiniPlayer ? 80 : 0,
            child: body,
          ),
          
          // 미니 플레이어
          if (showMiniPlayer)
            Positioned(
              left: 0,
              right: 0,
              bottom: bottomNavigationBar != null ? 80 : 0,
              child: MiniPlayerWidget(
                onTap: () => AudioPlayerUtils.showFullPlayer(context),
              ),
            ),
        ],
      ),
      bottomNavigationBar: bottomNavigationBar,
    );
  }
}

/// 간단한 스캐폴드 헬퍼
class SimpleAppScaffold extends ConsumerWidget {
  final String title;
  final Widget body;
  final List<Widget>? actions;
  final Widget? floatingActionButton;
  final bool showBackButton;

  const SimpleAppScaffold({
    super.key,
    required this.title,
    required this.body,
    this.actions,
    this.floatingActionButton,
    this.showBackButton = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AppScaffold(
      appBar: AppBar(
        title: Text(title),
        centerTitle: true,
        automaticallyImplyLeading: showBackButton,
        actions: actions,
      ),
      body: body,
      floatingActionButton: floatingActionButton,
    );
  }
}