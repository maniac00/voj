import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/book_model.dart';
import '../providers/auth_provider.dart';

class BookCard extends ConsumerWidget {
  final Book book;
  final VoidCallback? onTap;

  const BookCard({super.key, required this.book, this.onTap});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // authSessionProvider(StreamProvider)는 broadcast stream이라 초기 값을 놓칠 수 있음
    // currentSession은 동기적으로 항상 최신 세션을 반환
    final session = ref.watch(authRepositoryProvider).currentSession;
    final narrator = book.narrator?.trim();
    final hasNarrator = narrator != null && narrator.isNotEmpty;
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Semantics(
        label:
            '도서: ${book.title}, 저자: ${book.author}${hasNarrator ? ', 낭독: $narrator' : ''}, 상태: ${book.statusLabel ?? book.status.displayName}',
        hint: '탭하여 도서 상세 정보 보기',
        button: true,
        child: Material(
          color: const Color(0xFFFFFDF8),
          borderRadius: BorderRadius.circular(16),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(16),
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFC9A97A), width: 1.5),
              ),
              padding: const EdgeInsets.all(16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 책 표지
                  Container(
                    width: 100,
                    height: 140,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.15),
                          blurRadius: 6,
                          offset: const Offset(2, 3),
                        ),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: book.coverUrl != null
                          ? CachedNetworkImage(
                              imageUrl: book.coverUrl!,
                              fit: BoxFit.cover,
                              httpHeaders: {
                                if (session != null)
                                  'Authorization':
                                      'Bearer ${session.accessToken}',
                              },
                              errorWidget: (context, url, error) =>
                                  _buildDefaultCover(),
                            )
                          : _buildDefaultCover(),
                    ),
                  ),

                  const SizedBox(width: 16),

                  // 책 정보
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 제목
                        Text(
                          book.title,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF3E2723),
                            height: 1.3,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),

                        const SizedBox(height: 6),

                        // 저자 / 낭독자
                        Wrap(
                          spacing: 12,
                          runSpacing: 4,
                          children: [
                            Text(
                              '저자:${book.author}',
                              style: const TextStyle(
                                fontSize: 14,
                                color: Color(0xFF8D7B68),
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            if (hasNarrator)
                              Text(
                                '낭독:$narrator',
                                style: const TextStyle(
                                  fontSize: 14,
                                  color: Color(0xFF8D7B68),
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                          ],
                        ),

                        const SizedBox(height: 10),

                        // 챕터 수
                        Row(
                          children: [
                            const Icon(
                              Icons.music_note_rounded,
                              size: 16,
                              color: Color(0xFF8D7B68),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              '${book.chapterCount}개 챕터',
                              style: const TextStyle(
                                fontSize: 13,
                                color: Color(0xFF8D7B68),
                              ),
                            ),
                          ],
                        ),

                        // 설명
                        if (book.description != null &&
                            book.description!.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Text(
                            book.description!,
                            style: const TextStyle(
                              fontSize: 13,
                              color: Color(0xFF6D6050),
                              height: 1.5,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDefaultCover() {
    return Container(
      color: const Color(0xFF5D4037),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.book, color: Color(0xFFD7CCC8), size: 32),
          SizedBox(height: 4),
          Text(
            '오디오북',
            style: TextStyle(
              color: Color(0xFFD7CCC8),
              fontSize: 10,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
