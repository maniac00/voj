import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/book_model.dart';
import '../../data/services/local_playback_state.dart';
import '../providers/audio_player_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/book_provider.dart';
import '../screens/audio_player_screen.dart';

class BookDetailScreen extends ConsumerStatefulWidget {
  final Book book;

  const BookDetailScreen({
    super.key,
    required this.book,
  });

  @override
  ConsumerState<BookDetailScreen> createState() => _BookDetailScreenState();
}

class _BookDetailScreenState extends ConsumerState<BookDetailScreen> {
  SavedPlaybackState? _savedState;
  bool _isLoadingPlayback = false;

  @override
  void initState() {
    super.initState();
    _loadSavedState();
  }

  void _loadSavedState() {
    final prefs = ref.read(sharedPreferencesProvider);
    setState(() {
      _savedState = LocalPlaybackState.load(prefs, widget.book.id);
    });
  }

  @override
  Widget build(BuildContext context) {
    final bookDetailAsync = ref.watch(bookDetailProvider(widget.book.id));

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
      body: bookDetailAsync.when(
        data: (detailBook) => _buildBookDetail(context, ref, detailBook),
        loading: () => const Center(
          child: CircularProgressIndicator(
            color: Color(0xFF5D4037),
          ),
        ),
        error: (error, stack) => _buildErrorWidget(context, error),
      ),
    );
  }

  Widget _buildErrorWidget(BuildContext context, Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red[400]),
            const SizedBox(height: 16),
            Text(
              '오류가 발생했습니다',
              style: TextStyle(
                fontSize: 18,
                color: Colors.red[600],
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              getErrorMessage(error),
              style: const TextStyle(fontSize: 14),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Icons.arrow_back),
              label: const Text('돌아가기'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF5D4037),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBookDetail(BuildContext context, WidgetRef ref, Book book) {
    final session = ref.watch(authRepositoryProvider).currentSession;
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
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

          const SizedBox(height: 24),

          // 나무 액자 프레임 + 책 표지
          Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(6),
              border: Border.all(
                color: const Color(0xFF8B6914),
                width: 8,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.2),
                  blurRadius: 12,
                  offset: const Offset(3, 5),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(2),
              child: SizedBox(
                width: 160,
                height: 200,
                child: book.coverUrl != null
                    ? CachedNetworkImage(
                        imageUrl: book.coverUrl!,
                        fit: BoxFit.cover,
                        httpHeaders: {
                          if (session != null)
                            'Authorization': 'Bearer ${session.accessToken}',
                        },
                        errorWidget: (context, url, error) =>
                            _buildDefaultCover(),
                      )
                    : _buildDefaultCover(),
              ),
            ),
          ),

          const SizedBox(height: 20),

          // 저자 / 출판사 / 챕터 수
          Text(
            '저자: ${book.author}',
            style: const TextStyle(
              fontSize: 15,
              color: Color(0xFF5D4037),
              fontWeight: FontWeight.w500,
            ),
          ),
          if (book.publisher != null) ...[
            const SizedBox(height: 4),
            Text(
              '출판사: ${book.publisher}',
              style: const TextStyle(
                fontSize: 15,
                color: Color(0xFF5D4037),
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.music_note_rounded,
                size: 16,
                color: Color(0xFF5D4037),
              ),
              const SizedBox(width: 4),
              Text(
                '${book.chapterCount}개 챕터',
                style: const TextStyle(
                  fontSize: 15,
                  color: Color(0xFF5D4037),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // 재생 버튼
          SizedBox(
            width: double.infinity,
            height: 54,
            child: ElevatedButton(
              onPressed: () => _playFromSavedOrFirst(context, ref, book),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF5D4037),
                foregroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                _savedState != null
                    ? '\u25B6  ${_savedState!.resumeLabel}'
                    : '\u25B6  처음부터 재생 시작',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),

          const SizedBox(height: 28),

          // 내용 소개
          if (book.description != null && book.description!.isNotEmpty) ...[
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                '내용 소개',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF3E2723),
                ),
              ),
            ),
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                book.description!,
                style: const TextStyle(
                  fontSize: 14,
                  color: Color(0xFF5D4037),
                  height: 1.6,
                ),
              ),
            ),
            const SizedBox(height: 28),
          ],

          // 챕터 목록
          if (book.chapters.isNotEmpty) ...[
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                '챕터 목록',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF3E2723),
                ),
              ),
            ),
            const SizedBox(height: 12),
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFFC9A97A),
                  width: 1.5,
                ),
                color: const Color(0xFFFFFDF8),
              ),
              child: Column(
                children: [
                  for (int i = 0; i < book.chapters.length; i++) ...[
                    if (i > 0)
                      const Divider(
                        height: 1,
                        thickness: 1,
                        color: Color(0xFFE8DFD0),
                        indent: 16,
                        endIndent: 16,
                      ),
                    _buildChapterRow(book, book.chapters[i], ref),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildChapterRow(Book book, AudioChapter chapter, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Expanded(
            child: Text(
              chapter.displayName,
              style: const TextStyle(
                fontSize: 14,
                color: Color(0xFF3E2723),
                fontWeight: FontWeight.w500,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: () => _playSpecificAudioFile(context, ref, book, chapter),
            child: Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: Color(0xFF3E2723),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.play_arrow,
                color: Colors.white,
                size: 20,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDefaultCover() {
    return Container(
      color: const Color(0xFF5D4037),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.book, color: Color(0xFFD7CCC8), size: 40),
          SizedBox(height: 4),
          Text(
            '오디오북',
            style: TextStyle(
              color: Color(0xFFD7CCC8),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  /// 저장된 위치 또는 처음부터 재생
  void _playFromSavedOrFirst(BuildContext context, WidgetRef ref, Book book) {
    if (book.chapters.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('재생할 오디오 챕터가 없습니다')),
      );
      return;
    }

    if (_savedState != null) {
      // 저장된 챕터 찾기
      final savedChapter = book.chapters.where(
        (c) => c.id == _savedState!.chapterId,
      );
      if (savedChapter.isNotEmpty) {
        _playAndNavigate(
          context, ref, book, savedChapter.first,
          startPosition: _savedState!.positionSeconds,
        );
        return;
      }
    }

    // 첫 챕터부터 시작
    _playAndNavigate(context, ref, book, book.chapters.first);
  }

  /// 특정 오디오 파일 재생
  void _playSpecificAudioFile(BuildContext context, WidgetRef ref, Book book, AudioChapter chapter) {
    _playAndNavigate(context, ref, book, chapter);
  }

  /// 재생 시작 후 플레이어 화면으로 이동
  Future<void> _playAndNavigate(
    BuildContext context,
    WidgetRef ref,
    Book book,
    AudioChapter chapter, {
    int? startPosition,
  }) async {
    if (_isLoadingPlayback) return;
    _isLoadingPlayback = true;

    final controller = ref.read(audioPlayerControllerProvider);

    // 모달 오버레이 표시
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black54,
      builder: (context) => PopScope(
        canPop: false,
        child: Center(
          child: Card(
            color: const Color(0xFFFFFDF8),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Padding(
              padding: EdgeInsets.symmetric(horizontal: 32, vertical: 28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(
                    color: Color(0xFF5D4037),
                  ),
                  SizedBox(height: 20),
                  Text(
                    '재생을 준비하고 있습니다',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF3E2723),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );

    try {
      await controller.playChapter(
        book: book,
        chapter: chapter,
        playlist: book.chapters,
        startPosition: startPosition,
      );

      if (!context.mounted) return;
      Navigator.pop(context); // 모달 닫기

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => const AudioPlayerScreen(),
          fullscreenDialog: true,
        ),
      ).then((_) {
        _loadSavedState();
      });
    } catch (e) {
      if (!context.mounted) return;
      Navigator.pop(context); // 모달 닫기
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('재생 중 오류가 발생했습니다: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      _isLoadingPlayback = false;
    }
  }
}
