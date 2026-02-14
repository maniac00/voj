import 'dart:io';
import '../models/book_model.dart';
import '../../core/utils/logger.dart';
import 'api_service.dart';
import 'audio_service.dart';

const _log = AppLogger('BookService');

class BookService {
  final ApiService _apiService;
  final AudioService _audioService;

  BookService({ApiService? apiService, AudioService? audioService})
      : _apiService = apiService ?? ApiService(),
        _audioService = audioService ?? AudioService();

  void setAuthToken(String token) {
    _apiService.setAuthToken(token);
    _audioService.setAuthToken(token);
  }

  void clearAuthToken() {
    _apiService.clearAuthToken();
    _audioService.clearAuthToken();
  }

  /// 백엔드에 카테고리 목록 API가 아직 없으므로 빈 목록을 반환한다.
  Future<CategoriesResponse> getCategories() async {
    return const CategoriesResponse(message: '카테고리 정보가 없습니다', categories: []);
  }

  Future<BooksResponse> getBooks({
    int page = 1,
    int limit = 20,
    String? status,
    String? genre,
    String? search,
  }) async {
    try {
      final query = <String, dynamic>{
        'page': page,
        'size': limit,
        if (status != null && status.isNotEmpty) 'status': status,
        if (genre != null && genre.isNotEmpty) 'genre': genre,
        if (search != null && search.isNotEmpty) 'search': search,
      };

      final response = await _apiService.get('/books', queryParameters: query);
      final normalized = _normalizeBooksResponse(response, fallbackLimit: limit);
      // 목록 조회에서는 네트워크 비용을 줄이기 위해 챕터 목록을 추가 호출하지 않는다.
      // 상세 조회 시(getBookById) 챕터를 합성한다.
      return BooksResponse.fromJson(normalized);
    } on ApiException catch (error) {
      throw BookServiceException.fromApiException(error);
    } on SocketException {
      throw const BookServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (e, st) {
      _log.warning('도서 목록 조회 중 오류', error: e, stackTrace: st);
      throw const BookServiceException(
        message: '도서 목록 조회 중 오류가 발생했습니다',
        statusCode: -1,
      );
    }
  }

  Future<Book> getBookById(String bookId) async {
    try {
      final response = await _apiService.get('/books/$bookId');
      final payload = _ensureMap(response['book'] ?? response);
      final normalized = _normalizeBook(payload);

      final chapters = await _fetchChapters(bookId);
      normalized['chapters'] = chapters;
      normalized['_count'] = {
        'chapters': chapters.length,
      };

      return Book.fromJson(normalized);
    } on ApiException catch (error) {
      throw BookServiceException.fromApiException(error);
    } on SocketException {
      throw const BookServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (e, st) {
      _log.warning('도서 상세 정보 조회 중 오류', error: e, stackTrace: st);
      throw const BookServiceException(
        message: '도서 상세 정보 조회 중 오류가 발생했습니다',
        statusCode: -1,
      );
    }
  }

  Future<BookmarksResponse> getBookmarks({
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final response = await _apiService.get(
        '/books/bookmarks',
        queryParameters: {
          'page': page,
          'size': limit,
        },
      );
      return BookmarksResponse.fromJson(response);
    } on ApiException catch (error) {
      throw BookServiceException.fromApiException(error);
    } on SocketException {
      throw const BookServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (e, st) {
      _log.warning('북마크 목록 조회 중 오류', error: e, stackTrace: st);
      throw const BookServiceException(
        message: '북마크 목록 조회 중 오류가 발생했습니다',
        statusCode: -1,
      );
    }
  }

  Future<Bookmark> createBookmark({
    required String bookId,
    String? chapterId,
    required int position,
    String? note,
  }) async {
    try {
      final payload = {
        'book_id': bookId,
        if (chapterId != null) 'chapter_id': chapterId,
        'position': position,
        if (note != null) 'note': note,
      };

      final response = await _apiService.post('/books/bookmarks', body: payload);
      return Bookmark.fromJson(response['bookmark'] ?? response);
    } on ApiException catch (error) {
      throw BookServiceException.fromApiException(error);
    } on SocketException {
      throw const BookServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (e, st) {
      _log.warning('북마크 추가 중 오류', error: e, stackTrace: st);
      throw const BookServiceException(
        message: '북마크 추가 중 오류가 발생했습니다',
        statusCode: -1,
      );
    }
  }

  Future<void> deleteBookmark(String bookmarkId) async {
    try {
      await _apiService.delete('/books/bookmarks/$bookmarkId');
    } on ApiException catch (error) {
      throw BookServiceException.fromApiException(error);
    } on SocketException {
      throw const BookServiceException(
        message: '네트워크 연결을 확인해주세요',
        statusCode: 0,
      );
    } catch (e, st) {
      _log.warning('북마크 삭제 중 오류', error: e, stackTrace: st);
      throw const BookServiceException(
        message: '북마크 삭제 중 오류가 발생했습니다',
        statusCode: -1,
      );
    }
  }

  void dispose() {
    _apiService.dispose();
    _audioService.dispose();
  }

  Map<String, dynamic> _normalizeCategory(Map<String, dynamic> raw) {
    return {
      'id': raw['category_id'] ?? raw['id'] ?? '',
      'name': raw['name'] ?? '',
      'description': raw['description'],
      'createdAt': raw['created_at'] ?? raw['createdAt'] ?? DateTime.now().toIso8601String(),
      '_count': {
        'books': raw['book_count'] ?? raw['books'] ?? 0,
      },
    };
  }

  Map<String, dynamic> _normalizeBooksResponse(
    Map<String, dynamic> raw, {
    required int fallbackLimit,
  }) {
    final books = (raw['books'] as List<dynamic>? ?? [])
        .map((item) => _normalizeBook(_ensureMap(item)))
        .toList();
    final page = raw['page'] as int? ?? 1;
    final size = raw['size'] as int? ?? fallbackLimit;
    final total = raw['total'] as int? ?? books.length;
    final hasNext = raw['has_next'] as bool? ?? (page * size < total);
    final totalPages = size <= 0
        ? 1
        : (raw['total_pages'] as int?) ?? (hasNext ? page + 1 : (total / size).ceil());

    return {
      'message': raw['message'] ?? '도서 목록을 불러왔습니다',
      'books': books,
      'pagination': {
        'page': page,
        'limit': size,
        'total': total,
        'totalPages': totalPages,
        'hasNext': hasNext,
      },
    };
  }

  Map<String, dynamic> _normalizeBook(Map<String, dynamic> raw) {
    return {
      'id': raw['book_id'] ?? raw['id'] ?? '',
      'title': raw['title'] ?? '',
      'author': raw['author'] ?? '',
      'publisher': raw['publisher'],
      'categoryId': raw['category_id'] ?? raw['categoryId'] ?? '',
      'description': raw['description'],
      'coverUrl': raw['cover_image_url'] ?? raw['coverUrl'],
      'totalDuration': raw['total_duration'] ?? raw['totalDuration'] ?? 0,
      'status': (raw['status'] as String? ?? 'draft').toLowerCase(),
      'createdAt': raw['created_at'] ?? raw['createdAt'],
      'updatedAt': raw['updated_at'] ?? raw['updatedAt'],
      'publishedAt': raw['published_at'] ?? raw['publishedAt'],
      'genre': raw['genre'],
      'statusLabel': raw['status_label'] ?? raw['statusDisplay'],
      '_count': {
        'chapters': raw['total_chapters'] ?? raw['totalChapters'] ?? 0,
      },
      'chapters': raw['chapters'] ?? const [],
    };
  }

  Map<String, dynamic> _ensureMap(dynamic value) {
    if (value is Map<String, dynamic>) {
      return value;
    }
    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }
    throw const BookServiceException(
      message: '잘못된 응답 형식입니다',
      statusCode: -1,
    );
  }

  Future<List<Map<String, dynamic>>> _fetchChapters(String bookId) async {
    try {
      final response = await _audioService.getChapters(bookId: bookId);
      return response
          .map((chapter) => chapter.toJson())
          .map((json) {
            final mutable = Map<String, dynamic>.from(json);
            if (!mutable.containsKey('chapter_id')) {
              mutable['chapter_id'] = mutable['id'];
            }
            return mutable;
          })
          .toList();
    } on AudioServiceException catch (error) {
      if (error.isUnauthorized || error.isForbidden) {
        rethrow;
      }
      return const [];
    }
  }
}

class BookServiceException implements Exception {
  final String message;
  final int statusCode;
  final dynamic details;

  const BookServiceException({
    required this.message,
    required this.statusCode,
    this.details,
  });

  factory BookServiceException.fromApiException(ApiException error) {
    return BookServiceException(
      message: error.message,
      statusCode: error.statusCode,
      details: error.details,
    );
  }

  @override
  String toString() => 'BookServiceException: $message (Status: $statusCode)';

  bool get isNetworkError => statusCode == 0;
  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;
  bool get isValidationError => statusCode == 400;
}