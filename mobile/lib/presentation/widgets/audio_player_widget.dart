import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../providers/audio_player_provider.dart';
import '../providers/auth_provider.dart';
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
        color: const Color(0xFFFFFDF8),
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
                  color: const Color(0xFF5D4037),
                ),
                child: book.coverUrl != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: CachedNetworkImage(
                          imageUrl: book.coverUrl!,
                          fit: BoxFit.cover,
                          httpHeaders: {
                            if (ref.watch(authSessionProvider).valueOrNull != null)
                              'Authorization': 'Bearer ${ref.watch(authSessionProvider).valueOrNull!.accessToken}',
                          },
                          errorWidget: (context, url, error) =>
                              const Icon(Icons.book, size: 32, color: Color(0xFFD7CCC8)),
                        ),
                      )
                    : const Icon(Icons.book, size: 32, color: Color(0xFFD7CCC8)),
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
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF3E2723),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      chapter.displayName,
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF8D7B68),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),

              // 재생 컨트롤
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    onPressed: controller.skipToPrevious,
                    icon: const Icon(Icons.skip_previous, color: Color(0xFF3E2723)),
                    iconSize: 28,
                    tooltip: '이전 챕터',
                  ),

                  Container(
                    width: 44,
                    height: 44,
                    decoration: const BoxDecoration(
                      color: Color(0xFF5D2E0C),
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
                      tooltip: playerState.when(
                        data: (state) => state.playing ? '일시정지' : '재생',
                        loading: () => '로딩 중',
                        error: (_, __) => '오류',
                      ),
                      icon: playerState.when(
                        data: (state) => Icon(
                          state.playing ? Icons.pause : Icons.play_arrow,
                          color: Colors.white,
                          size: 22,
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
                          size: 22,
                        ),
                      ),
                    ),
                  ),

                  IconButton(
                    onPressed: controller.skipToNext,
                    icon: const Icon(Icons.skip_next, color: Color(0xFF3E2723)),
                    iconSize: 28,
                    tooltip: '다음 챕터',
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
    final isReady = playerState.whenOrNull(
      data: (state) =>
          state.processingState == ProcessingState.ready ||
          state.processingState == ProcessingState.completed,
    ) ?? false;

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
      child: Column(
        children: [
          // 책 커버
          Container(
            width: 100,
            height: 130,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              color: const Color(0xFF5D4037),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.25),
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: book.coverUrl != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: CachedNetworkImage(
                      imageUrl: book.coverUrl!,
                      fit: BoxFit.cover,
                      httpHeaders: {
                        if (ref.watch(authSessionProvider).valueOrNull != null)
                          'Authorization': 'Bearer ${ref.watch(authSessionProvider).valueOrNull!.accessToken}',
                      },
                      errorWidget: (context, url, error) =>
                          _buildDefaultCover(),
                    ),
                  )
                : _buildDefaultCover(),
          ),
          const SizedBox(height: 32),

          // 책 제목
          Text(
            book.title,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: Color(0xFF3E2723),
              height: 1.3,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 8),

          // 저자
          Text(
            book.author,
            style: const TextStyle(
              fontSize: 16,
              color: Color(0xFF5D4037),
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),

          // 챕터 제목
          Text(
            chapter.displayName,
            style: const TextStyle(
              fontSize: 14,
              color: Color(0xFF8D7B68),
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 28),

          // 진행률 슬라이더
          _buildProgressSlider(context, ref, controller, position, duration),
          const SizedBox(height: 40),

          // 재생 컨트롤
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // 이전 트랙
              _buildControlButton(
                onPressed: isReady ? controller.skipToPrevious : null,
                icon: Icons.skip_previous,
                size: 48,
                iconSize: 26,
              ),

              // 10초 뒤로
              _buildControlButton(
                onPressed: isReady ? () {
                  position.when(
                    data: (pos) {
                      final newPosition = pos - const Duration(seconds: 10);
                      controller.seek(newPosition < Duration.zero ? Duration.zero : newPosition);
                    },
                    loading: () {},
                    error: (error, stack) {},
                  );
                } : null,
                icon: Icons.replay_10,
                size: 48,
                iconSize: 26,
              ),

              // 재생/일시정지 (큰 버튼)
              _buildPlayButton(context, controller, playerState, isReady),

              // 10초 앞으로
              _buildControlButton(
                onPressed: isReady ? () {
                  position.when(
                    data: (pos) {
                      duration.when(
                        data: (dur) {
                          if (dur != null) {
                            final newPosition = pos + const Duration(seconds: 10);
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
                } : null,
                icon: Icons.forward_10,
                size: 48,
                iconSize: 26,
              ),

              // 다음 트랙
              _buildControlButton(
                onPressed: isReady ? controller.skipToNext : null,
                icon: Icons.skip_next,
                size: 48,
                iconSize: 26,
              ),
            ],
          ),
          const SizedBox(height: 32),

          // 재생 속도 조절
          _buildSpeedControl(context, ref, controller, speed),
        ],
      ),
    );
  }

  Widget _buildControlButton({
    required VoidCallback? onPressed,
    required IconData icon,
    required double size,
    required double iconSize,
  }) {
    final enabled = onPressed != null;
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: enabled ? const Color(0xFF3E2723) : const Color(0xFFBCAAA4),
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: enabled ? const Color(0xFFF5EDE0) : const Color(0xFFD7CCC8),
          size: iconSize,
        ),
      ),
    );
  }

  Widget _buildPlayButton(
    BuildContext context,
    AudioPlayerController controller,
    AsyncValue<PlayerState> playerState,
    bool isReady,
  ) {
    return GestureDetector(
      onTap: isReady ? () {
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
      } : null,
      child: Container(
        width: 76,
        height: 76,
        decoration: BoxDecoration(
          color: isReady ? const Color(0xFF5D2E0C) : const Color(0xFFBCAAA4),
          shape: BoxShape.circle,
        ),
        child: playerState.when(
          data: (state) {
            if (state.processingState == ProcessingState.loading ||
                state.processingState == ProcessingState.buffering) {
              return const Center(
                child: SizedBox(
                  width: 32,
                  height: 32,
                  child: CircularProgressIndicator(
                    strokeWidth: 3,
                    valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFF5EDE0)),
                  ),
                ),
              );
            }
            return Icon(
              state.playing ? Icons.pause : Icons.play_arrow,
              color: const Color(0xFFF5EDE0),
              size: 40,
            );
          },
          loading: () => const Center(
            child: SizedBox(
              width: 32,
              height: 32,
              child: CircularProgressIndicator(
                strokeWidth: 3,
                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFF5EDE0)),
              ),
            ),
          ),
          error: (error, stack) => const Icon(
            Icons.error,
            color: Color(0xFFF5EDE0),
            size: 40,
          ),
        ),
      ),
    );
  }

  Widget _buildDefaultCover() {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Container(
        color: const Color(0xFF5D4037),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.book, color: Color(0xFFD7CCC8), size: 48),
            SizedBox(height: 8),
            Text(
              '오디오북',
              style: TextStyle(
                color: Color(0xFFD7CCC8),
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
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
                  trackHeight: 6,
                  activeTrackColor: const Color(0xFF5D4037),
                  inactiveTrackColor: const Color(0xFFC9A97A),
                  thumbColor: const Color(0xFF5D4037),
                  thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 8),
                  overlayShape: const RoundSliderOverlayShape(overlayRadius: 16),
                  overlayColor: const Color(0x295D4037),
                ),
                child: Slider(
                  value: totalSeconds > 0
                      ? (currentSeconds / totalSeconds).clamp(0.0, 1.0)
                      : 0,
                  onChanged: (value) {
                    if (totalSeconds > 0) {
                      final newPosition = Duration(seconds: (value * totalSeconds).round());
                      controller.seek(newPosition);
                    }
                  },
                  semanticFormatterCallback: (value) {
                    final seconds = (value * totalSeconds).round();
                    final min = seconds ~/ 60;
                    final sec = seconds % 60;
                    return '$min분 $sec초';
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
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF3E2723),
                      ),
                    ),
                    Text(
                      dur != null ? _formatDuration(dur) : '--:--',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF3E2723),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
        loading: () => const LinearProgressIndicator(
          color: Color(0xFF5D4037),
          backgroundColor: Color(0xFFC9A97A),
        ),
        error: (error, stack) => const SizedBox(),
      ),
      loading: () => const LinearProgressIndicator(
        color: Color(0xFF5D4037),
        backgroundColor: Color(0xFFC9A97A),
      ),
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
      data: (currentSpeed) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: const Color(0xFFC9A97A),
            width: 1.5,
          ),
          color: const Color(0xFFFFFDF8),
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<double>(
            value: currentSpeed,
            isDense: true,
            icon: const Icon(
              Icons.keyboard_arrow_down,
              color: Color(0xFF3E2723),
              size: 20,
            ),
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Color(0xFF3E2723),
            ),
            dropdownColor: const Color(0xFFFFFDF8),
            items: speeds.map((s) {
              return DropdownMenuItem(
                value: s,
                child: Text('${s}x'),
              );
            }).toList(),
            onChanged: (newSpeed) {
              if (newSpeed != null) {
                controller.setSpeed(newSpeed);
              }
            },
          ),
        ),
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
