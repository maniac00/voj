import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../providers/audio_player_provider.dart';
import '../../data/models/book_model.dart';

/// 오디오 플레이어 위젯
class AudioPlayerWidget extends ConsumerWidget {
  final bool isFullPlayer;
  final VoidCallback? onTap;

  const AudioPlayerWidget({
    super.key,
    this.isFullPlayer = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentBook = ref.watch(currentBookProvider);
    final currentChapter = ref.watch(currentChapterProvider);
    final playerState = ref.watch(playerStateProvider);
    final position = ref.watch(positionProvider);
    final duration = ref.watch(durationProvider);
    final speed = ref.watch(speedProvider);
    final chapterStatus = ref.watch(currentChapterStatusProvider);
    final controller = ref.read(audioPlayerControllerProvider);

    if (currentBook == null || currentChapter == null) {
      return const SizedBox.shrink();
    }

    return isFullPlayer 
        ? _buildFullPlayer(context, ref, controller, currentBook, currentChapter, 
                          playerState, position, duration, speed, chapterStatus)
        : _buildMiniPlayer(context, ref, controller, currentBook, currentChapter, 
                          playerState, position, duration, chapterStatus);
  }

  Widget _buildMiniPlayer(
    BuildContext context,
    WidgetRef ref,
    AudioPlayerController controller,
    Book book,
    AudioChapter chapter,
    AsyncValue<PlayerState> playerState,
    AsyncValue<Duration> position,
    AsyncValue<Duration?> duration,
    String? chapterStatus,
  ) {
    return Container(
      height: 80,
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Row(
            children: [
              // 책 커버
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  color: Colors.grey[300],
                ),
                child: book.coverUrl != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          book.coverUrl!,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) =>
                              const Icon(Icons.book, size: 32),
                        ),
                      )
                    : const Icon(Icons.book, size: 32),
              ),
              const SizedBox(width: 12),
              
              // 책 정보
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      book.title,
                      style: Theme.of(context).textTheme.titleSmall,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      chapter.fileName,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (chapterStatus != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        '상태: $chapterStatus',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
              
              // 재생 컨트롤
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // 이전 트랙
                  IconButton(
                    onPressed: controller.skipToPrevious,
                    icon: const Icon(Icons.skip_previous),
                    iconSize: 28,
                  ),
                  
                  // 재생/일시정지
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Theme.of(context).primaryColor,
                      shape: BoxShape.circle,
                    ),
                    child: IconButton(
                      onPressed: () {
                        playerState.when(
                          data: (state) {
                            if (state.playing) {
                              controller.pause();
                            } else {
                              controller.resume();
                            }
                          },
                          loading: () {},
                          error: (error, stack) {},
                        );
                      },
                      icon: playerState.when(
                        data: (state) => Icon(
                          state.playing ? Icons.pause : Icons.play_arrow,
                          color: Colors.white,
                        ),
                        loading: () => const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        ),
                        error: (error, stack) => const Icon(
                          Icons.error,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  
                  // 다음 트랙
                  IconButton(
                    onPressed: controller.skipToNext,
                    icon: const Icon(Icons.skip_next),
                    iconSize: 28,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFullPlayer(
    BuildContext context,
    WidgetRef ref,
    AudioPlayerController controller,
    Book book,
    AudioChapter chapter,
    AsyncValue<PlayerState> playerState,
    AsyncValue<Duration> position,
    AsyncValue<Duration?> duration,
    AsyncValue<double> speed,
    String? chapterStatus,
  ) {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // 책 커버
          Container(
            width: 200,
            height: 200,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              color: Colors.grey[300],
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.2),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: book.coverUrl != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.network(
                      book.coverUrl!,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) =>
                          const Icon(Icons.book, size: 80),
                    ),
                  )
                : const Icon(Icons.book, size: 80),
          ),
          const SizedBox(height: 32),
          
          // 책 제목과 저자
          Text(
            book.title,
            style: Theme.of(context).textTheme.headlineSmall,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 8),
          Text(
            book.author,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Colors.grey[600],
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            chapter.fileName,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[500],
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          if (chapterStatus != null) ...[
            const SizedBox(height: 4),
            Text(
              '상태: $chapterStatus',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 32),
          
          // 진행률 슬라이더
          _buildProgressSlider(context, ref, controller, position, duration),
          const SizedBox(height: 32),
          
          // 재생 컨트롤
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // 이전 트랙
              IconButton(
                onPressed: controller.skipToPrevious,
                icon: const Icon(Icons.skip_previous),
                iconSize: 40,
              ),
              
              // 15초 뒤로
              IconButton(
                onPressed: () {
                  position.when(
                    data: (pos) {
                      final newPosition = pos - const Duration(seconds: 15);
                      controller.seek(newPosition < Duration.zero ? Duration.zero : newPosition);
                    },
                    loading: () {},
                    error: (error, stack) {},
                  );
                },
                icon: const Icon(Icons.replay),
                iconSize: 32,
              ),
              
              // 재생/일시정지
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor,
                  shape: BoxShape.circle,
                ),
                child: IconButton(
                  onPressed: () {
                    playerState.when(
                      data: (state) {
                        if (state.playing) {
                          controller.pause();
                        } else {
                          controller.resume();
                        }
                      },
                      loading: () {},
                      error: (error, stack) {},
                    );
                  },
                  icon: playerState.when(
                    data: (state) => Icon(
                      state.playing ? Icons.pause : Icons.play_arrow,
                      color: Colors.white,
                      size: 36,
                    ),
                    loading: () => const SizedBox(
                      width: 32,
                      height: 32,
                      child: CircularProgressIndicator(
                        strokeWidth: 3,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                    error: (error, stack) => const Icon(
                      Icons.error,
                      color: Colors.white,
                      size: 36,
                    ),
                  ),
                ),
              ),
              
              // 15초 앞으로
              IconButton(
                onPressed: () {
                  position.when(
                    data: (pos) {
                      duration.when(
                        data: (dur) {
                          if (dur != null) {
                            final newPosition = pos + const Duration(seconds: 15);
                            controller.seek(newPosition > dur ? dur : newPosition);
                          }
                        },
                        loading: () {},
                        error: (error, stack) {},
                      );
                    },
                    loading: () {},
                    error: (error, stack) {},
                  );
                },
                icon: const Icon(Icons.fast_forward),
                iconSize: 32,
              ),
              
              // 다음 트랙
              IconButton(
                onPressed: controller.skipToNext,
                icon: const Icon(Icons.skip_next),
                iconSize: 40,
              ),
            ],
          ),
          const SizedBox(height: 24),
          
          // 재생 속도 조절
          _buildSpeedControl(context, ref, controller, speed),
        ],
      ),
    );
  }

  Widget _buildProgressSlider(
    BuildContext context,
    WidgetRef ref,
    AudioPlayerController controller,
    AsyncValue<Duration> position,
    AsyncValue<Duration?> duration,
  ) {
    return position.when(
      data: (pos) => duration.when(
        data: (dur) {
          final totalSeconds = dur?.inSeconds ?? 0;
          final currentSeconds = pos.inSeconds;
          
          return Column(
            children: [
              SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  trackHeight: 4,
                  thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 8),
                  overlayShape: const RoundSliderOverlayShape(overlayRadius: 16),
                ),
                child: Slider(
                  value: totalSeconds > 0 ? currentSeconds / totalSeconds : 0,
                  onChanged: (value) {
                    if (totalSeconds > 0) {
                      final newPosition = Duration(seconds: (value * totalSeconds).round());
                      controller.seek(newPosition);
                    }
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatDuration(pos),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                    Text(
                      dur != null ? _formatDuration(dur) : '--:--',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          );
        },
        loading: () => const LinearProgressIndicator(),
        error: (error, stack) => const SizedBox(),
      ),
      loading: () => const LinearProgressIndicator(),
      error: (error, stack) => const SizedBox(),
    );
  }

  Widget _buildSpeedControl(
    BuildContext context,
    WidgetRef ref,
    AudioPlayerController controller,
    AsyncValue<double> speed,
  ) {
    final speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
    
    return speed.when(
      data: (currentSpeed) => Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.speed, size: 20),
          const SizedBox(width: 8),
          DropdownButton<double>(
            value: currentSpeed,
            underline: const SizedBox(),
            items: speeds.map((speed) {
              return DropdownMenuItem(
                value: speed,
                child: Text('${speed}x'),
              );
            }).toList(),
            onChanged: (newSpeed) {
              if (newSpeed != null) {
                controller.setSpeed(newSpeed);
              }
            },
          ),
        ],
      ),
      loading: () => const SizedBox(),
      error: (error, stack) => const SizedBox(),
    );
  }

  String _formatDuration(Duration duration) {
    final minutes = duration.inMinutes;
    final seconds = duration.inSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
}

/// 미니 플레이어 위젯
class MiniPlayerWidget extends ConsumerWidget {
  final VoidCallback? onTap;

  const MiniPlayerWidget({
    super.key,
    this.onTap,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final showMiniPlayer = ref.watch(showMiniPlayerProvider);
    
    if (!showMiniPlayer) {
      return const SizedBox.shrink();
    }

    return AudioPlayerWidget(
      isFullPlayer: false,
      onTap: onTap,
    );
  }
}