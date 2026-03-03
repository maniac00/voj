import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/book_model.dart';
import '../providers/auth_provider.dart';
import '../providers/book_provider.dart';
import '../widgets/book_card.dart';
import '../widgets/search_bar_widget.dart';
import 'book_detail_screen.dart';

class BooksScreen extends ConsumerStatefulWidget {
  const BooksScreen({super.key});

  @override
  ConsumerState<BooksScreen> createState() => _BooksScreenState();
}

class _BooksScreenState extends ConsumerState<BooksScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(booksProvider.notifier).loadBooks();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadMoreBooks();
    }
  }

  void _loadMoreBooks() {
    final booksState = ref.read(booksProvider);
    final searchState = ref.read(searchProvider);

    if (booksState is AsyncData &&
        booksState.value?.pagination.hasNext == true) {
      final nextPage = booksState.value!.pagination.page + 1;
      String? searchQuery;

      if (searchState is SearchSearching) {
        searchQuery = searchState.query;
      }

      ref.read(booksProvider.notifier).loadMoreBooks(
        nextPage: nextPage,
        search: searchQuery,
        status: null,
        genre: null,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final booksState = ref.watch(booksProvider);
    final searchState = ref.watch(searchProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF5EDE0),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF5EDE0),
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        automaticallyImplyLeading: false,
        leading: IconButton(
          onPressed: () => _refreshBooks(),
          icon: const Icon(Icons.refresh, color: Color(0xFF3E2723)),
          tooltip: '새로고침',
        ),
        title: const Text(
          '도서 목록',
          style: TextStyle(
            color: Color(0xFF3E2723),
            fontWeight: FontWeight.w700,
            fontSize: 20,
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            onPressed: () => _showSearchDialog(),
            icon: const Icon(Icons.search, color: Color(0xFF3E2723)),
            tooltip: '검색',
          ),
          IconButton(
            onPressed: () => _showLogoutDialog(),
            icon: const Icon(Icons.logout, color: Color(0xFF3E2723)),
            tooltip: '로그아웃',
          ),
        ],
      ),
      body: Column(
        children: [
          // 검색 상태 표시
          if (searchState is SearchSearching)
            Container(
              width: double.infinity,
              color: const Color(0xFFE8DFD0),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              child: Row(
                children: [
                  const Icon(Icons.search, color: Color(0xFF5D4037), size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '검색: "${searchState.query}"',
                      style: const TextStyle(
                        color: Color(0xFF5D4037),
                        fontWeight: FontWeight.w500,
                        fontSize: 14,
                      ),
                    ),
                  ),
                  GestureDetector(
                    onTap: () => _clearSearch(),
                    child: const Icon(Icons.close,
                        color: Color(0xFF5D4037), size: 20),
                  ),
                ],
              ),
            ),

          // 정렬 선택
          _buildSortBar(),

          // 도서 목록
          Expanded(
            child: booksState.when(
              data: (response) => _buildBookList(response),
              loading: () => const Center(
                child: CircularProgressIndicator(
                  color: Color(0xFF5D4037),
                ),
              ),
              error: (error, stack) => _buildErrorWidget(error),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSortBar() {
    final sortOrder = ref.watch(bookSortOrderProvider);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          _buildSortChip(
            label: '최근 재생순',
            selected: sortOrder == BookSortOrder.recentlyPlayed,
            onTap: () => ref.read(bookSortOrderProvider.notifier).state = BookSortOrder.recentlyPlayed,
          ),
          const SizedBox(width: 8),
          _buildSortChip(
            label: '최신순',
            selected: sortOrder == BookSortOrder.newest,
            onTap: () => ref.read(bookSortOrderProvider.notifier).state = BookSortOrder.newest,
          ),
          const SizedBox(width: 8),
          _buildSortChip(
            label: '가나다순',
            selected: sortOrder == BookSortOrder.alphabetical,
            onTap: () => ref.read(bookSortOrderProvider.notifier).state = BookSortOrder.alphabetical,
          ),
        ],
      ),
    );
  }

  Widget _buildSortChip({
    required String label,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF5D4037) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? const Color(0xFF5D4037) : const Color(0xFFBCAAA4),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: selected ? Colors.white : const Color(0xFF5D4037),
          ),
        ),
      ),
    );
  }

  List<Book> _sortBooks(List<Book> books) {
    final sortOrder = ref.read(bookSortOrderProvider);
    final sorted = List<Book>.from(books);
    switch (sortOrder) {
      case BookSortOrder.recentlyPlayed:
        final prefs = ref.read(sharedPreferencesProvider);
        final recentlyPlayedJson = prefs.getString('recently_played_books');
        final Map<String, int> recentlyPlayedMap = recentlyPlayedJson != null
            ? Map<String, int>.from(json.decode(recentlyPlayedJson))
            : {};
        sorted.sort((a, b) {
          final aTime = recentlyPlayedMap[a.id] ?? 0;
          final bTime = recentlyPlayedMap[b.id] ?? 0;
          if (aTime == 0 && bTime == 0) return b.createdAt.compareTo(a.createdAt);
          if (aTime == 0) return 1;
          if (bTime == 0) return -1;
          return bTime.compareTo(aTime);
        });
      case BookSortOrder.newest:
        sorted.sort((a, b) => b.createdAt.compareTo(a.createdAt));
      case BookSortOrder.alphabetical:
        sorted.sort((a, b) => a.title.compareTo(b.title));
    }
    return sorted;
  }

  Widget _buildBookList(BooksResponse response) {
    if (response.books.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.book_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '도서가 없습니다',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '다른 검색어를 시도해보세요',
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    final sortedBooks = _sortBooks(response.books);

    return RefreshIndicator(
      color: const Color(0xFF5D4037),
      onRefresh: () async => _refreshBooks(),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        itemCount:
            sortedBooks.length + (response.pagination.hasNext ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= sortedBooks.length) {
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(
                child: CircularProgressIndicator(color: Color(0xFF5D4037)),
              ),
            );
          }

          final book = sortedBooks[index];
          return BookCard(
            book: book,
            onTap: () => _navigateToBookDetail(book),
          );
        },
      ),
    );
  }

  Widget _buildErrorWidget(Object error) {
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
              onPressed: _refreshBooks,
              icon: const Icon(Icons.refresh),
              label: const Text('다시 시도'),
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

  void _showSearchDialog() {
    showDialog(
      context: context,
      builder: (context) => SearchBarWidget(
        onSearch: (query) {
          Navigator.of(context).pop();
          _performSearch(query);
        },
      ),
    );
  }

  void _performSearch(String query) {
    if (query.trim().isEmpty) {
      _clearSearch();
      return;
    }

    ref.read(searchProvider.notifier).setQuery(query);
    ref.read(booksProvider.notifier).loadBooks(
      search: query,
      status: null,
      genre: null,
      forceRefresh: true,
    );
  }

  void _clearSearch() {
    ref.read(searchProvider.notifier).clearSearch();
    ref.read(booksProvider.notifier).loadBooks(
      status: null,
      genre: null,
      forceRefresh: true,
    );
  }

  void _refreshBooks() {
    final searchState = ref.read(searchProvider);
    String? searchQuery;

    if (searchState is SearchSearching) {
      searchQuery = searchState.query;
    }

    ref.read(booksProvider.notifier).loadBooks(
      search: searchQuery,
      status: null,
      genre: null,
      forceRefresh: true,
    );
  }

  void _navigateToBookDetail(Book book) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => BookDetailScreen(book: book),
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('로그아웃'),
          content: const Text('정말로 로그아웃하시겠습니까?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                ref.read(authControllerProvider.notifier).logout();
                Navigator.of(this.context).pushReplacementNamed('/login');
              },
              child: const Text('로그아웃'),
            ),
          ],
        );
      },
    );
  }
}
