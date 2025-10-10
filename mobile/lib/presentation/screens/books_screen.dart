import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/models/book_model.dart';
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
    
    // 초기 데이터 로드
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
      appBar: AppBar(
        title: const Text('도서 목록'),
        centerTitle: true,
        elevation: 1,
        actions: [
          IconButton(
            onPressed: () => _showSearchDialog(),
            icon: const Icon(Icons.search),
            tooltip: '검색',
          ),
          IconButton(
            onPressed: () => _refreshBooks(),
            icon: const Icon(Icons.refresh),
            tooltip: '새로고침',
          ),
        ],
      ),
      body: Column(
        children: [
          // 검색 상태 표시
          if (searchState is SearchSearching)
            Container(
              width: double.infinity,
              color: Theme.of(context).primaryColor.withValues(alpha: 0.1),
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Icon(
                    Icons.search,
                    color: Theme.of(context).primaryColor,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '검색: "${searchState.query}"',
                      style: TextStyle(
                        color: Theme.of(context).primaryColor,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: () => _clearSearch(),
                    icon: const Icon(Icons.close),
                    tooltip: '검색 취소',
                  ),
                ],
              ),
            ),
          
          // 카테고리 필터 제거
          const SizedBox.shrink(),
          
          // 도서 목록
          Expanded(
            child: booksState.when(
              data: (response) => _buildBookList(response),
              loading: () => const Center(
                child: CircularProgressIndicator(),
              ),
              error: (error, stack) => _buildErrorWidget(error),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBookList(BooksResponse response) {
    if (response.books.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.book_outlined,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              '도서가 없습니다',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '다른 카테고리를 선택해보세요',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => _refreshBooks(),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        itemCount: response.books.length + (response.pagination.hasNext ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= response.books.length) {
            // 로딩 인디케이터
            return const Padding(
              padding: EdgeInsets.all(16),
              child: Center(child: CircularProgressIndicator()),
            );
          }

          final book = response.books[index];
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
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.red[400],
            ),
            const SizedBox(height: 16),
            Text(
              '오류가 발생했습니다',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: Colors.red[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              getErrorMessage(error),
              style: Theme.of(context).textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _refreshBooks,
              icon: const Icon(Icons.refresh),
              label: const Text('다시 시도'),
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
}