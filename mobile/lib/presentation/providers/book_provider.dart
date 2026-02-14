import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/utils/logger.dart';
import '../../data/models/book_model.dart';
import '../../data/repositories/book_repository.dart';
import '../../data/services/book_service.dart';
import 'auth_provider.dart';
import '../../core/constants/app_config.dart';

const _log = AppLogger('BookProvider');

// Export the service exception for use in UI
export '../../data/services/book_service.dart' show BookServiceException;

// Book 서비스 프로바이더
final bookServiceProvider = Provider<BookService>((ref) {
  return BookService();
});

// Book 저장소 프로바이더
final bookRepositoryProvider = Provider<BookRepository>((ref) {
  final bookService = ref.watch(bookServiceProvider);
  final authRepo = ref.watch(authRepositoryProvider);
  final bookRepo = BookRepository(
    bookService: bookService,
    authRepository: authRepo,
  );

  final initialSession = authRepo.currentSession;
  if (!AppConfig.authBypassEnabled) {
    if (initialSession != null && initialSession.isValid) {
      bookRepo.setAuthToken(initialSession.accessToken);
    }
  } else {
    bookRepo.clearAuthToken();
  }

  ref.listen(authSessionProvider, (previous, next) {
    if (AppConfig.authBypassEnabled) {
      bookRepo.clearAuthToken();
      return;
    }
    next.when(
      data: (session) {
        if (session != null && session.isValid) {
          bookRepo.setAuthToken(session.accessToken);
        } else {
          bookRepo.clearAuthToken();
        }
      },
      loading: () {},
      error: (_, __) => bookRepo.clearAuthToken(),
    );
  });

  return bookRepo;
});

// 도서 목록 프로바이더
class BooksNotifier extends StateNotifier<AsyncValue<BooksResponse>> {
  final BookRepository _bookRepository;
  
  BooksNotifier(this._bookRepository) : super(const AsyncValue.loading());

  Future<void> loadBooks({
    int page = 1,
    int limit = 20,
    String? search,
    String? status,
    String? genre,
    bool forceRefresh = false,
  }) async {
    state = const AsyncValue.loading();
    
    try {
      final response = await _bookRepository.getBooks(
        page: page,
        limit: limit,
        search: search,
        status: status,
        genre: genre,
        forceRefresh: forceRefresh,
      );
      state = AsyncValue.data(response);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> loadMoreBooks({
    required int nextPage,
    int limit = 20,
    String? search,
    String? status,
    String? genre,
  }) async {
    final currentState = state;
    if (currentState is! AsyncData<BooksResponse>) return;
    
    try {
      final response = await _bookRepository.getBooks(
        page: nextPage,
        limit: limit,
        search: search,
        status: status,
        genre: genre,
      );
      
      // 기존 데이터와 새 데이터 합치기
      final currentBooks = currentState.value.books;
      final newBooks = [...currentBooks, ...response.books];
      
      final updatedResponse = BooksResponse(
        message: response.message,
        books: newBooks,
        pagination: response.pagination,
      );
      
      state = AsyncValue.data(updatedResponse);
    } catch (error) {
      // 더 로드 실패 시 기존 상태 유지하고 에러는 별도 처리
      _log.warning('더 로드 실패', error: error);
    }
  }

  void refresh() {
    loadBooks(forceRefresh: true);
  }
}

// 도서 목록 상태 프로바이더
final booksProvider = StateNotifierProvider<BooksNotifier, AsyncValue<BooksResponse>>((ref) {
  final bookRepo = ref.watch(bookRepositoryProvider);
  return BooksNotifier(bookRepo);
});

// 특정 도서 상세 프로바이더
final bookDetailProvider = FutureProvider.family<Book, String>((ref, bookId) async {
  final bookRepo = ref.watch(bookRepositoryProvider);
  return await bookRepo.getBookById(bookId);
});

// 북마크 목록 프로바이더
class BookmarksNotifier extends StateNotifier<AsyncValue<BookmarksResponse>> {
  final BookRepository _bookRepository;
  
  BookmarksNotifier(this._bookRepository) : super(const AsyncValue.loading());

  Future<void> loadBookmarks({
    int page = 1,
    int limit = 20,
  }) async {
    state = const AsyncValue.loading();
    
    try {
      final response = await _bookRepository.getBookmarks(
        page: page,
        limit: limit,
      );
      state = AsyncValue.data(response);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> addBookmark({
    required String bookId,
    String? chapterId,
    required int position,
    String? note,
  }) async {
    try {
      await _bookRepository.createBookmark(
        bookId: bookId,
        chapterId: chapterId,
        position: position,
        note: note,
      );
      
      // 북마크 목록 새로고침
      loadBookmarks();
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> removeBookmark(String bookmarkId) async {
    try {
      await _bookRepository.deleteBookmark(bookmarkId);
      
      // 북마크 목록 새로고침
      loadBookmarks();
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  void refresh() {
    loadBookmarks();
  }
}

// 북마크 목록 상태 프로바이더
final bookmarksProvider = StateNotifierProvider<BookmarksNotifier, AsyncValue<BookmarksResponse>>((ref) {
  final bookRepo = ref.watch(bookRepositoryProvider);
  return BookmarksNotifier(bookRepo);
});

// 검색 상태 프로바이더
class SearchNotifier extends StateNotifier<SearchState> {
  SearchNotifier() : super(const SearchState.initial());

  void setQuery(String query) {
    state = SearchState.searching(query);
  }

  void clearSearch() {
    state = const SearchState.initial();
  }
}

final searchProvider = StateNotifierProvider<SearchNotifier, SearchState>((ref) {
  return SearchNotifier();
});

// 검색 상태 클래스
sealed class SearchState {
  const SearchState();

  const factory SearchState.initial() = SearchInitial;
  const factory SearchState.searching(String query) = SearchSearching;
}

class SearchInitial extends SearchState {
  const SearchInitial();
}

class SearchSearching extends SearchState {
  final String query;
  const SearchSearching(this.query);
}

// 현재 재생 중인 책 프로바이더 (추후 오디오 플레이어와 연동)
final currentPlayingBookProvider = StateProvider<Book?>((ref) => null);

// 유틸리티: 에러 메시지 추출
String getErrorMessage(dynamic error) {
  if (error is BookServiceException) {
    return error.message;
  }
  return '알 수 없는 오류가 발생했습니다';
}
