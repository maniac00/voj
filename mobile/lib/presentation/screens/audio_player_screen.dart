import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/audio_player_provider.dart';
import '../widgets/audio_player_widget.dart';
import '../../data/models/book_model.dart';

/// 전체 화면 오디오 플레이어 스크린
class AudioPlayerScreen extends ConsumerStatefulWidget {
  const AudioPlayerScreen({super.key});

  @override
  ConsumerState<AudioPlayerScreen> createState() => _AudioPlayerScreenState();
}

class _AudioPlayerScreenState extends ConsumerState<AudioPlayerScreen> {
  bool _showPlaylist = false;

  @override
  Widget build(BuildContext context) {
    final currentBook = ref.watch(currentBookProvider);
    final currentChapter = ref.watch(currentChapterProvider);
    final playlist = ref.watch(playlistProvider);
    final currentIndex = ref.watch(currentIndexProvider);

    if (currentBook == null || currentChapter == null) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('오디오 플레이어'),
        ),
        body: const Center(
          child: Text('재생 중인 오디오가 없습니다'),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.keyboard_arrow_down),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('재생 중'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(_showPlaylist ? Icons.close : Icons.queue_music),
            onPressed: () {
              setState(() {
                _showPlaylist = !_showPlaylist;
              });
            },
          ),
        ],
      ),
      body: _showPlaylist 
          ? _buildPlaylistView(playlist, currentIndex)
          : const AudioPlayerWidget(isFullPlayer: true),
    );
  }

  Widget _buildPlaylistView(List<AudioChapter>? playlist, int currentIndex) {
    if (playlist == null || playlist.isEmpty) {
      return const Center(
        child: Text('플레이리스트가 비어있습니다'),
      );
    }

    return Column(
      children: [
        // 플레이리스트 헤더
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Theme.of(context).cardColor,
            border: Border(
              bottom: BorderSide(
                color: Colors.grey.withValues(alpha: 0.2),
              ),
            ),
          ),
          child: Row(
            children: [
              const Icon(Icons.queue_music),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '플레이리스트',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    Text(
                      '${playlist.length}개 트랙',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        
        // 플레이리스트 목록
        Expanded(
          child: ListView.builder(
            itemCount: playlist.length,
            itemBuilder: (context, index) {
              final audioChapter = playlist[index];
              final isCurrentTrack = index == currentIndex;
              
              return ListTile(
                leading: Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: isCurrentTrack 
                        ? Theme.of(context).primaryColor 
                        : Colors.grey[300],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Center(
                    child: isCurrentTrack
                        ? const Icon(
                            Icons.volume_up,
                            color: Colors.white,
                            size: 20,
                          )
                        : Text(
                            '${audioChapter.chapterNumber}',
                            style: const TextStyle(
                              color: Colors.black54,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                  ),
                ),
                title: Text(
                  audioChapter.fileName,
                  style: TextStyle(
                    fontWeight: isCurrentTrack ? FontWeight.bold : FontWeight.normal,
                    color: isCurrentTrack ? Theme.of(context).primaryColor : null,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                subtitle: Text(audioChapter.durationText),
                trailing: isCurrentTrack
                    ? Icon(
                        Icons.equalizer,
                        color: Theme.of(context).primaryColor,
                      )
                    : null,
                onTap: () {
                  // 선택한 트랙 재생
                  final controller = ref.read(audioPlayerControllerProvider);
                  final currentBook = ref.read(currentBookProvider);
                  
                  if (currentBook != null) {
                    controller.playChapter(
                      book: currentBook,
                      chapter: audioChapter,
                      playlist: playlist,
                    );
                  }
                  
                  // 플레이어 뷰로 돌아가기
                  setState(() {
                    _showPlaylist = false;
                  });
                },
              );
            },
          ),
        ),
      ],
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
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(
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
            content: Text('${chapter.fileName} 재생 시작'),
            duration: const Duration(seconds: 2),
            action: SnackBarAction(
              label: '플레이어 열기',
              onPressed: () => showFullPlayer(context),
            ),
          ),
        );
      }
    } catch (e) {
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