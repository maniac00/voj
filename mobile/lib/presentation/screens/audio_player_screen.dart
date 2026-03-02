import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/audio_player_provider.dart';
import '../providers/auth_provider.dart';
import '../widgets/audio_player_widget.dart';
import '../../data/models/book_model.dart';
import '../../data/services/local_playback_state.dart';

/// 전체 화면 오디오 플레이어 스크린
class AudioPlayerScreen extends ConsumerStatefulWidget {
  const AudioPlayerScreen({super.key});

  @override
  ConsumerState<AudioPlayerScreen> createState() => _AudioPlayerScreenState();
}

class _AudioPlayerScreenState extends ConsumerState<AudioPlayerScreen> {
  bool _showPlaylist = false;

  Future<void> _goBack() async {
    // 현재 재생 위치를 로컬에 저장
    final book = ref.read(currentBookProvider);
    final chapter = ref.read(currentChapterProvider);
    final service = ref.read(audioPlayerServiceProvider);
    if (book != null && chapter != null) {
      final prefs = ref.read(sharedPreferencesProvider);
      // 완료 상태에서 position이 0으로 리셋될 수 있으므로 duration을 사용
      var positionSec = service.position.inSeconds;
      final durationSec = service.duration?.inSeconds ?? 0;
      if (positionSec <= 0 && durationSec > 0) {
        positionSec = durationSec;
      }
      LocalPlaybackState.save(
        prefs,
        bookId: book.id,
        chapterId: chapter.id,
        chapterNumber: chapter.chapterNumber,
        chapterFileName: chapter.displayName,
        positionSeconds: positionSec,
      );
    }
    await ref.read(audioPlayerControllerProvider).stop();
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final currentBook = ref.watch(currentBookProvider);
    final currentChapter = ref.watch(currentChapterProvider);
    final playlist = ref.watch(playlistProvider);
    final currentIndex = ref.watch(currentIndexProvider);

    if (currentBook == null || currentChapter == null) {
      return Scaffold(
        backgroundColor: const Color(0xFFF5EDE0),
        appBar: AppBar(
          backgroundColor: const Color(0xFFF5EDE0),
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: Color(0xFF3E2723)),
            tooltip: '이전',
            onPressed: _goBack,
          ),
          title: const Text(
            '재생 중',
            style: TextStyle(
              color: Color(0xFF3E2723),
              fontWeight: FontWeight.w700,
              fontSize: 20,
            ),
          ),
          centerTitle: true,
        ),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(color: Color(0xFF5D4037)),
              SizedBox(height: 16),
              Text(
                '책을 불러오는 중입니다.\n잠시만 기다려 주세요.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF5D4037)),
              ),
            ],
          ),
        ),
      );
    }

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) {
          if (_showPlaylist) {
            setState(() => _showPlaylist = false);
          } else {
            _goBack();
          }
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFF5EDE0),
        appBar: _showPlaylist
            ? _buildPlaylistAppBar()
            : _buildPlayerAppBar(),
        body: SafeArea(
          child: _showPlaylist
              ? _buildPlaylistView(playlist, currentIndex)
              : const AudioPlayerWidget(isFullPlayer: true),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildPlayerAppBar() {
    return AppBar(
      backgroundColor: const Color(0xFFF5EDE0),
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: Color(0xFF3E2723)),
        tooltip: '이전',
        onPressed: _goBack,
      ),
      title: const Text(
        '재생 중',
        style: TextStyle(
          color: Color(0xFF3E2723),
          fontWeight: FontWeight.w700,
          fontSize: 20,
        ),
      ),
      centerTitle: true,
      actions: [
        IconButton(
          icon: const Icon(Icons.queue_music, color: Color(0xFF3E2723)),
          tooltip: '플레이리스트',
          onPressed: () => setState(() => _showPlaylist = true),
        ),
      ],
    );
  }

  PreferredSizeWidget _buildPlaylistAppBar() {
    return AppBar(
      backgroundColor: const Color(0xFFF5EDE0),
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back, color: Color(0xFF3E2723)),
        tooltip: '플레이어로 돌아가기',
        onPressed: () => setState(() => _showPlaylist = false),
      ),
      title: const Text(
        '플레이리스트',
        style: TextStyle(
          color: Color(0xFF3E2723),
          fontWeight: FontWeight.w700,
          fontSize: 20,
        ),
      ),
      centerTitle: true,
    );
  }

  Widget _buildPlaylistView(List<AudioChapter>? playlist, int currentIndex) {
    if (playlist == null || playlist.isEmpty) {
      return const Center(
        child: Text(
          '플레이리스트가 비어있습니다',
          style: TextStyle(color: Color(0xFF5D4037), fontSize: 16),
        ),
      );
    }

    return Column(
      children: [
        // 플레이리스트 헤더
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Row(
            children: [
              const Icon(
                Icons.auto_stories,
                color: Color(0xFF5D4037),
                size: 22,
              ),
              const SizedBox(width: 10),
              Text(
                '플레이리스트 (${playlist.length}개 트랙)',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF3E2723),
                ),
              ),
            ],
          ),
        ),

        // 트랙 목록
        Expanded(
          child: ListView.builder(
            itemCount: playlist.length,
            padding: const EdgeInsets.only(bottom: 24),
            itemBuilder: (context, index) {
              final chapter = playlist[index];
              final isCurrentTrack = index == currentIndex;

              return _buildTrackItem(
                chapter: chapter,
                isCurrentTrack: isCurrentTrack,
                playlist: playlist,
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildTrackItem({
    required AudioChapter chapter,
    required bool isCurrentTrack,
    required List<AudioChapter> playlist,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: isCurrentTrack ? const Color(0xFFE8DFD0) : Colors.transparent,
        border: const Border(
          bottom: BorderSide(
            color: Color(0xFFE0D5C5),
            width: 0.5,
          ),
        ),
      ),
      child: InkWell(
        onTap: () {
          final controller = ref.read(audioPlayerControllerProvider);
          final currentBook = ref.read(currentBookProvider);

          if (currentBook != null) {
            controller.playChapter(
              book: currentBook,
              chapter: chapter,
              playlist: playlist,
            );
          }

          setState(() => _showPlaylist = false);
        },
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          child: Row(
            children: [
              // 아이콘
              if (isCurrentTrack)
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    color: const Color(0xFFC9A97A),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.graphic_eq,
                    color: Color(0xFF5D2E0C),
                    size: 22,
                  ),
                )
              else
                SizedBox(
                  width: 36,
                  height: 36,
                  child: Icon(
                    Icons.auto_stories_outlined,
                    color: const Color(0xFF8D7B68),
                    size: 24,
                  ),
                ),

              const SizedBox(width: 14),

              // 트랙 정보
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      chapter.displayName,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: isCurrentTrack ? FontWeight.w700 : FontWeight.w500,
                        color: isCurrentTrack
                            ? const Color(0xFF3E2723)
                            : const Color(0xFF5D4037),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      chapter.durationText,
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF8D7B68),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(width: 12),

              // 재생 버튼
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: const Color(0xFF3E2723),
                    width: 2,
                  ),
                ),
                child: const Icon(
                  Icons.play_arrow,
                  color: Color(0xFF3E2723),
                  size: 20,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// 오디오 플레이어 모달 바텀시트
class AudioPlayerBottomSheet extends ConsumerWidget {
  const AudioPlayerBottomSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DraggableScrollableSheet(
      initialChildSize: 0.9,
      minChildSize: 0.5,
      maxChildSize: 1.0,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Color(0xFFF5EDE0),
            borderRadius: BorderRadius.vertical(
              top: Radius.circular(20),
            ),
          ),
          child: const AudioPlayerScreen(),
        );
      },
    );
  }
}

/// 오디오 플레이어 관련 유틸리티
class AudioPlayerUtils {
  /// 전체 화면 오디오 플레이어 표시
  static void showFullPlayer(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const AudioPlayerScreen(),
        fullscreenDialog: true,
      ),
    );
  }

  /// 모달 바텀시트로 오디오 플레이어 표시
  static void showPlayerBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const AudioPlayerBottomSheet(),
    );
  }

  /// 오디오 파일 재생 시작
  static Future<void> playAudio(
    BuildContext context,
    WidgetRef ref, {
    required Book book,
    required AudioChapter chapter,
    List<AudioChapter>? playlist,
    int? startPosition,
  }) async {
    try {
      final controller = ref.read(audioPlayerControllerProvider);

      await controller.playChapter(
        book: book,
        chapter: chapter,
        playlist: playlist,
        startPosition: startPosition,
      );

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${chapter.displayName} 재생 시작'),
            duration: const Duration(seconds: 2),
            action: SnackBarAction(
              label: '플레이어 열기',
              onPressed: () => showFullPlayer(context),
            ),
          ),
        );
      }
    } catch (e) {
      // Loading interrupted — 사용자가 빠르게 다른 트랙을 선택한 경우 무시
      if (e.toString().contains('Loading interrupted')) return;
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('재생 중 오류가 발생했습니다: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// 시간 포맷 (분:초)
  static String formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  /// 시간 포맷 (시:분:초 또는 분:초)
  static String formatDetailedDuration(Duration duration) {
    final hours = duration.inHours;
    final minutes = duration.inMinutes % 60;
    final seconds = duration.inSeconds % 60;

    if (hours > 0) {
      return '$hours:${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
    } else {
      return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
    }
  }
}
