import 'dart:async';
import '../models/book_model.dart';
import '../services/book_service.dart';
import 'auth_repository.dart';

/// TTL 기반 캐시 항목
class _CacheEntry<T> {
  final T value;
  final DateTime expiresAt;

  _CacheEntry(this.value, {Duration ttl = const Duration(minutes: 5)})
      : expiresAt = DateTime.now().add(ttl);

  bool get isExpired => DateTime.now().isAfter(expiresAt);
}

class BookRepository {
  final BookService _bookService;
  final AuthRepository _authRepository;

  // TTL 기반 캐시
  _CacheEntry<List<Category>>? _cachedCategories;
  final Map<String, _CacheEntry<Book>> _cachedBooks = {};
  final Map<String, _CacheEntry<List<Book>>> _cachedBookLists = {};
  
  BookRepository({required BookService bookService, required AuthRepository authRepository})
      : _bookService = bookService,
        _authRepository = authRepository;

  void setAuthToken(String token) {
    _bookService.setAuthToken(token);
  }

  void clearAuthToken() {
    _bookService.clearAuthToken();
    _clearCache();
  }

  void _clearCache() {
    _cachedCategories = null;
    _cachedBooks.clear();
    _cachedBookLists.clear();
  }

  // 카테고리 목록 조회 (현재 백엔드에서 미제공)
  Future<List<Category>> getCategories({bool forceRefresh = false}) async {
    if (!forceRefresh && _cachedCategories != null && !_cachedCategories!.isExpired) {
      return _cachedCategories!.value;
    }

    // 백엔드에 카테고리 엔드포인트가 없으므로 빈 배열을 반환한다.
    _cachedCategories = _CacheEntry(const []);
    return _cachedCategories!.value;
  }

  // 도서 목록 조회
  Future<BooksResponse> getBooks({
    int page = 1,
    int limit = 20,
    String? search,
    String? status,
    String? genre,
    bool forceRefresh = false,
  }) async {
    final cacheKey = 'books_${page}_${limit}_${status ?? 'all'}_${genre ?? 'all'}_${search ?? ''}';

    if (!forceRefresh && _cachedBookLists.containsKey(cacheKey) && !_cachedBookLists[cacheKey]!.isExpired) {
      // 캐시된 데이터가 있으면 반환
      final books = _cachedBookLists[cacheKey]!.value;
      return BooksResponse(
        message: '캐시된 도서 목록',
        books: books,
        pagination: PaginationInfo(
          page: page,
          limit: limit,
          total: books.length,
          totalPages: (books.length / limit).ceil(),
          hasNext: false,
        ),
      );
    }

    try {
      final response = await _bookService.getBooks(
        page: page,
        limit: limit,
        search: search,
        status: status,
        genre: genre,
      );

      // 캐시 업데이트
      _cachedBookLists[cacheKey] = _CacheEntry(response.books);

      // 개별 책 캐시도 업데이트
      for (final book in response.books) {
        _cachedBooks[book.id] = _CacheEntry(book);
      }

      return response;
    } catch (e) {
      await _handleAuthError(e);
      rethrow;
    }
  }

  // 도서 상세 조회
  Future<Book> getBookById(String bookId, {bool forceRefresh = false}) async {
    if (!forceRefresh && _cachedBooks.containsKey(bookId) && !_cachedBooks[bookId]!.isExpired) {
      final cached = _cachedBooks[bookId]!.value;
      // 목록 캐시에는 챕터 정보가 비어 있을 수 있으므로, 비어 있으면 강제 새로고침
      if (cached.chapters.isNotEmpty) {
        return cached;
      }
      // fallthrough to refresh when chapters are empty
    }

    try {
      final book = await _bookService.getBookById(bookId);
      _cachedBooks[bookId] = _CacheEntry(book);
      return book;
    } catch (e) {
      await _handleAuthError(e);
      rethrow;
    }
  }

  // 검색 결과 캐시 클리어
  void clearSearchCache() {
    _cachedBookLists.removeWhere((key, value) => key.contains('search'));
  }

  // 특정 카테고리 캐시 클리어
  void clearCategoryCache(String categoryId) {
    _cachedBookLists.removeWhere((key, value) => key.contains(categoryId));
  }

  void dispose() {
    _clearCache();
    _bookService.dispose();
  }

  Future<void> _handleAuthError(dynamic error) async {
    if (error is BookServiceException && (error.isUnauthorized || error.isForbidden)) {
      await _authRepository.handleUnauthorized();
    }
  }
}
