import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/book_model.dart';
import '../providers/book_provider.dart';
import '../widgets/accessibility_button.dart';
import '../screens/audio_player_screen.dart';

class BookDetailScreen extends ConsumerWidget {
  final Book book;

  const BookDetailScreen({
    super.key,
    required this.book,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bookDetailAsync = ref.watch(bookDetailProvider(book.id));

    return Scaffold(
      appBar: AppBar(
        title: Text(book.title),
        centerTitle: true,
        actions: [
          IconButton(
            onPressed: null,
            icon: const Icon(Icons.favorite_border),
            tooltip: '즐겨찾기 (준비 중)',
          ),
        ],
      ),
      body: bookDetailAsync.when(
        data: (detailBook) => _buildBookDetail(context, ref, detailBook),
        loading: () => const Center(
          child: CircularProgressIndicator(),
        ),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.red[400],
              ),
              const SizedBox(height: 16),
              Text(
                '오류가 발생했습니다',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(
                getErrorMessage(error),
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('돌아가기'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBookDetail(BuildContext context, WidgetRef ref, Book book) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 책 정보 카드
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 책 표지
                  Container(
                    width: 120,
                    height: 180,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                      border: Border.all(
                        color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
                      ),
                    ),
                    child: book.coverUrl != null
                        ? ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: CachedNetworkImage(
                              imageUrl: book.coverUrl!,
                              fit: BoxFit.cover,
                              errorWidget: (context, url, error) =>
                                  _buildDefaultCover(context),
                            ),
                          )
                        : _buildDefaultCover(context),
                  ),
                  
                  const SizedBox(width: 20),
                  
                  // 책 정보
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          book.title,
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        
                        const SizedBox(height: 8),
                        
                        Text(
                          '저자: ${book.author}',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: Colors.grey[700],
                          ),
                        ),
                        
                        if (book.publisher != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            '출판사: ${book.publisher}',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                        
                        const SizedBox(height: 12),
                        
                        if (book.category != null)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 6,
                            ),
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.primary,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              book.category!.name,
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        
                        const SizedBox(height: 16),
                        
                        Row(
                          children: [
                            Icon(
                              Icons.access_time,
                              size: 20,
                              color: Colors.grey[600],
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '총 재생시간: ${book.durationText}',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                        
                        const SizedBox(height: 8),
                        
                        Row(
                          children: [
                            Icon(
                              Icons.audiotrack,
                              size: 20,
                              color: Colors.grey[600],
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '${book.chapterCount}개 챕터',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          
          // 재생 버튼
          AccessibilityButton(
            onPressed: () => _playFirstAudioFile(context, ref, book),
            text: '재생 시작',
            icon: Icons.play_arrow,
          ),
          
          const SizedBox(height: 16),
          
          // 북마크 추가 버튼
          AccessibilityButton(
            onPressed: () => _showBookmarkDialog(context),
            text: '북마크 추가',
            icon: Icons.bookmark_add,
            backgroundColor: Colors.grey[600],
          ),
          
          const SizedBox(height: 24),
          
          // 책 설명
          if (book.description != null && book.description!.isNotEmpty) ...[
            Text(
              '내용 소개',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[200]!),
              ),
              child: Text(
                book.description!,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  height: 1.5,
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
          
          // 챕터 목록
          if (book.chapters.isNotEmpty) ...[
            Text(
              '챕터 목록',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            ...book.chapters.map((chapter) {
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    child: Text(
                      '${chapter.chapterNumber}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  title: Text(
                    chapter.fileName.replaceAll('.mp3', ''),
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                  subtitle: Text(
                    '재생시간: ${chapter.durationText}',
                  ),
                  trailing: IconButton(
                    onPressed: () => _playSpecificAudioFile(context, ref, book, chapter),
                    icon: const Icon(Icons.play_arrow),
                    tooltip: '재생',
                  ),
                ),
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildDefaultCover(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Theme.of(context).colorScheme.primary.withValues(alpha: 0.7),
            Theme.of(context).colorScheme.primary.withValues(alpha: 0.5),
          ],
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.book,
            color: Colors.white,
            size: 48,
          ),
          const SizedBox(height: 8),
          Text(
            '오디오북',
            style: TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  void _showBookmarkDialog(BuildContext context) {
    final noteController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('북마크 추가'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('이 위치에 북마크를 추가하시겠습니까?'),
            const SizedBox(height: 16),
            TextField(
              controller: noteController,
              decoration: const InputDecoration(
                labelText: '메모 (선택사항)',
                hintText: '북마크에 대한 메모를 입력하세요',
              ),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              // TODO: 실제 북마크 추가 구현
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('북마크가 추가되었습니다')),
              );
            },
            child: const Text('추가'),
          ),
        ],
      ),
    );
  }

  /// 첫 번째 오디오 파일 재생
  void _playFirstAudioFile(BuildContext context, WidgetRef ref, Book book) {
    if (book.chapters.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('재생할 오디오 챕터가 없습니다')),
      );
      return;
    }

    final firstChapter = book.chapters.first;
    AudioPlayerUtils.playAudio(
      context,
      ref,
      book: book,
      chapter: firstChapter,
      playlist: book.chapters,
    );
  }

  /// 특정 오디오 파일 재생
  void _playSpecificAudioFile(BuildContext context, WidgetRef ref, Book book, AudioChapter chapter) {
    AudioPlayerUtils.playAudio(
      context,
      ref,
      book: book,
      chapter: chapter,
      playlist: book.chapters,
    );
  }
}