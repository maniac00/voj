import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:voice_of_juan/data/models/book_model.dart';
import 'package:voice_of_juan/data/services/api_service.dart';
import 'package:voice_of_juan/data/services/book_service.dart';

class StubApiService extends ApiService {
  final Map<String, Map<String, dynamic>> _responses;

  StubApiService(this._responses)
      : super(client: http.Client(), baseUrl: 'http://localhost');

  @override
  Future<Map<String, dynamic>> request({
    required String method,
    required String path,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? body,
  }) async {
    final key = '${method.toUpperCase()} $path';
    final response = _responses[key];
    if (response == null) {
      throw const ApiException(message: 'Stub response not found', statusCode: 404);
    }
    return response;
  }
}

void main() {
  group('BookService', () {
    test('getBooks normalizes response fields', () async {
      final stub = StubApiService({
        'GET /books': {
          'message': 'success',
          'books': [
            {
              'book_id': 'book-1',
              'title': 'Demo Book',
              'author': '홍길동',
              'status': 'DRAFT',
              'status_label': '작성중',
              'total_duration': 5400,
              'total_chapters': 3,
              'genre': 'essay',
              'created_at': '2024-01-01T00:00:00Z',
              'updated_at': '2024-01-02T00:00:00Z',
            }
          ],
          'total': 1,
          'page': 1,
          'size': 10,
          'has_next': false,
        },
      });

      final service = BookService(apiService: stub);
      final response = await service.getBooks();

      expect(response.message, 'success');
      expect(response.pagination.hasNext, isFalse);
      expect(response.pagination.totalPages, 1);
      expect(response.books, hasLength(1));

      final book = response.books.first;
      expect(book.id, 'book-1');
      expect(book.totalDuration, 5400);
      expect(book.audioFileCount, 3);
      expect(book.status, BookStatus.draft);
      expect(book.statusLabel, '작성중');
      expect(book.genre, 'essay');
    });

    test('getBookById parses single book payload', () async {
      final stub = StubApiService({
        'GET /books/book-2': {
          'book': {
            'book_id': 'book-2',
            'title': 'Another Book',
            'author': '이몽룡',
            'status': 'ARCHIVED',
            'status_label': '보관됨',
            'total_duration': 1200,
            'total_chapters': 1,
            'created_at': '2024-02-01T00:00:00Z',
            'updated_at': '2024-02-02T00:00:00Z',
          }
        },
      });

      final service = BookService(apiService: stub);
      final book = await service.getBookById('book-2');

      expect(book.id, 'book-2');
      expect(book.status, BookStatus.archived);
      expect(book.statusLabel, '보관됨');
      expect(book.audioFileCount, 1);
    });
  });
}
