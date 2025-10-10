class Category {
  final String id;
  final String name;
  final String? description;
  final DateTime createdAt;
  final int bookCount;

  Category({
    required this.id,
    required this.name,
    this.description,
    DateTime? createdAt,
    this.bookCount = 0,
  }) : createdAt = createdAt ?? DateTime.now();

  factory Category.fromJson(Map<String, dynamic> json) {
    final createdAtRaw = json['createdAt'] ?? json['created_at'];
    final countRaw = json['_count']?['books'] ?? json['bookCount'] ?? json['count'];
    final id = json['id'] as String? ?? json['categoryId'] as String? ?? '';

    return Category(
      id: id,
      name: json['name'] as String? ?? id,
      description: json['description'] as String?,
      createdAt: _parseDateTime(createdAtRaw) ?? DateTime.now(),
      bookCount: _parseInt(countRaw),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'description': description,
      'createdAt': createdAt.toIso8601String(),
      'bookCount': bookCount,
    };
  }

  Category copyWith({
    String? id,
    String? name,
    String? description,
    DateTime? createdAt,
    int? bookCount,
  }) {
    return Category(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      createdAt: createdAt ?? this.createdAt,
      bookCount: bookCount ?? this.bookCount,
    );
  }
}

DateTime? _parseDateTime(dynamic value) {
  if (value is DateTime) {
    return value.toUtc();
  }
  if (value is String && value.isNotEmpty) {
    try {
      return DateTime.parse(value).toUtc();
    } catch (_) {
      return null;
    }
  }
  return null;
}

int _parseInt(dynamic value) {
  if (value is int) {
    return value;
  }
  if (value is String) {
    return int.tryParse(value) ?? 0;
  }
  return 0;
}

class Book {
  final String id;
  final String title;
  final String author;
  final String? publisher;
  final String categoryId;
  final String? description;
  final String? coverUrl;
  final int totalDuration; // in seconds
  final BookStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? publishedAt;
  final Category? category;
  final List<AudioFile> audioFiles;
  final int audioFileCount;
  final String? userId;
  final String? statusLabel;
  final String? genre;

  const Book({
    required this.id,
    required this.title,
    required this.author,
    this.publisher,
    required this.categoryId,
    this.description,
    this.coverUrl,
    required this.totalDuration,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.publishedAt,
    this.category,
    this.audioFiles = const [],
    this.audioFileCount = 0,
    this.userId,
    this.statusLabel,
    this.genre,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    final createdAtRaw = json['createdAt'] ?? json['created_at'];
    final updatedAtRaw = json['updatedAt'] ?? json['updated_at'];
    final publishedAtRaw = json['publishedAt'] ?? json['published_at'];

    final createdAt = _parseDateTime(createdAtRaw) ?? DateTime.now();
    final updatedAt = _parseDateTime(updatedAtRaw) ?? createdAt;
    final publishedAt = _parseDateTime(publishedAtRaw);

    final statusValue = (json['status'] as String? ?? 'draft').toLowerCase();
    final totalDurationRaw = json['totalDuration'] ?? json['total_duration'];
    final audioFileCountRaw = json['_count']?['audioFiles'] ?? json['audioFileCount'] ?? json['total_chapters'];
    final statusLabel = json['statusLabel'] ?? json['status_label'] ?? json['status_display'] ?? json['statusDisplay'];

    return Book(
      id: json['id'] as String? ?? json['book_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      author: json['author'] as String? ?? '',
      publisher: json['publisher'] as String?,
      categoryId: json['categoryId'] as String? ?? json['category_id'] as String? ?? '',
      description: json['description'] as String?,
      coverUrl: json['coverUrl'] as String? ?? json['cover_image_url'] as String?,
      totalDuration: _parseInt(totalDurationRaw),
      status: BookStatus.values.firstWhere(
        (value) => value.name == statusValue,
        orElse: () => BookStatus.values.firstWhere(
          (value) => value.value.toLowerCase() == statusValue,
          orElse: () => BookStatus.draft,
        ),
      ),
      createdAt: createdAt,
      updatedAt: updatedAt,
      publishedAt: publishedAt,
      category: json['category'] != null
          ? Category.fromJson(Map<String, dynamic>.from(json['category'] as Map))
          : null,
      audioFiles: json['audioFiles'] != null
          ? (json['audioFiles'] as List)
              .whereType<Map<String, dynamic>>()
              .map(AudioFile.fromJson)
              .toList()
          : const [],
      audioFileCount: _parseInt(audioFileCountRaw),
      userId: json['user_id'] as String?,
      statusLabel: statusLabel as String?,
      genre: json['genre'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'author': author,
      'publisher': publisher,
      'categoryId': categoryId,
      'description': description,
      'coverUrl': coverUrl,
      'totalDuration': totalDuration,
      'status': status.name,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
      'publishedAt': publishedAt?.toIso8601String(),
      'audioFileCount': audioFileCount,
      'userId': userId,
      'statusLabel': statusLabel,
      'genre': genre,
    };
  }

  Book copyWith({
    String? id,
    String? title,
    String? author,
    String? publisher,
    String? categoryId,
    String? description,
    String? coverUrl,
    int? totalDuration,
    BookStatus? status,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? publishedAt,
    Category? category,
    List<AudioFile>? audioFiles,
    int? audioFileCount,
    String? userId,
    String? statusLabel,
    String? genre,
  }) {
    return Book(
      id: id ?? this.id,
      title: title ?? this.title,
      author: author ?? this.author,
      publisher: publisher ?? this.publisher,
      categoryId: categoryId ?? this.categoryId,
      description: description ?? this.description,
      coverUrl: coverUrl ?? this.coverUrl,
      totalDuration: totalDuration ?? this.totalDuration,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      publishedAt: publishedAt ?? this.publishedAt,
      category: category ?? this.category,
      audioFiles: audioFiles ?? this.audioFiles,
      audioFileCount: audioFileCount ?? this.audioFileCount,
      userId: userId ?? this.userId,
      statusLabel: statusLabel ?? this.statusLabel,
      genre: genre ?? this.genre,
    );
  }

  String get durationText {
    final hours = totalDuration ~/ 3600;
    final minutes = (totalDuration % 3600) ~/ 60;
    
    if (hours > 0) {
      return '$hours시간 $minutes분';
    } else {
      return '$minutes분';
    }
  }
}

class AudioFile {
  final String id;
  final String bookId;
  final String fileName;
  final String? fileUrl;
  final int? fileSize;
  final int duration; // in seconds
  final int sequence;
  final AudioFileStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? statusLabel;

  const AudioFile({
    required this.id,
    required this.bookId,
    required this.fileName,
    this.fileUrl,
    this.fileSize,
    required this.duration,
    required this.sequence,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.statusLabel,
  });

  factory AudioFile.fromJson(Map<String, dynamic> json) {
    return AudioFile(
      id: json['id'] as String? ?? json['chapter_id'] as String? ?? '',
      bookId: json['bookId'] as String? ?? json['book_id'] as String? ?? '',
      fileName: json['fileName'] as String? ?? json['file_name'] as String? ?? '',
      fileUrl: json['fileUrl'] as String? ?? json['file_url'] as String?,
      fileSize: json['fileSize'] as int? ?? json['file_size'] as int?,
      duration: json['duration'] as int? ?? json['duration_seconds'] as int? ?? 0,
      sequence: json['sequence'] as int? ?? json['chapter_number'] as int? ?? 0,
      status: AudioFileStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? '').toLowerCase(),
        orElse: () => AudioFileStatus.processing,
      ),
      createdAt: _parseDateTime(json['createdAt'] ?? json['created_at']) ?? DateTime.now(),
      updatedAt: _parseDateTime(json['updatedAt'] ?? json['updated_at']) ?? DateTime.now(),
      statusLabel: json['status_label'] as String? ?? json['statusDisplay'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'bookId': bookId,
      'fileName': fileName,
      'fileUrl': fileUrl,
      'fileSize': fileSize,
      'duration': duration,
      'sequence': sequence,
      'status': status.name,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
      'statusLabel': statusLabel,
    };
  }

  String get durationText {
    final minutes = duration ~/ 60;
    final seconds = duration % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
}

class Bookmark {
  final String id;
  final String userId;
  final String bookId;
  final String? audioFileId;
  final int position; // in seconds
  final String? note;
  final DateTime createdAt;
  final Book? book;
  final AudioFile? audioFile;

  const Bookmark({
    required this.id,
    required this.userId,
    required this.bookId,
    this.audioFileId,
    required this.position,
    this.note,
    required this.createdAt,
    this.book,
    this.audioFile,
  });

  factory Bookmark.fromJson(Map<String, dynamic> json) {
    return Bookmark(
      id: json['id'] as String? ?? json['bookmark_id'] as String? ?? '',
      userId: json['userId'] as String? ?? json['user_id'] as String? ?? '',
      bookId: json['bookId'] as String? ?? json['book_id'] as String? ?? '',
      audioFileId: json['audioFileId'] as String? ?? json['chapter_id'] as String?,
      position: _parseInt(json['position'] ?? json['position_seconds']),
      note: json['note'] as String?,
      createdAt: _parseDateTime(json['createdAt'] ?? json['created_at']) ?? DateTime.now(),
      book: json['book'] != null
          ? Book.fromJson(Map<String, dynamic>.from(json['book'] as Map))
          : null,
      audioFile: json['audioFile'] != null
          ? AudioFile.fromJson(Map<String, dynamic>.from(json['audioFile'] as Map))
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'userId': userId,
      'bookId': bookId,
      'audioFileId': audioFileId,
      'position': position,
      'note': note,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  String get positionText {
    final hours = position ~/ 3600;
    final minutes = (position % 3600) ~/ 60;
    final seconds = position % 60;
    
    if (hours > 0) {
      return '$hours:${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
    } else {
      return '$minutes:${seconds.toString().padLeft(2, '0')}';
    }
  }
}

enum BookStatus {
  draft('DRAFT', '작성중'),
  published('PUBLISHED', '출간'),
  archived('ARCHIVED', '보관됨');

  const BookStatus(this.value, this.displayName);
  final String value;
  final String displayName;
}

enum AudioFileStatus {
  processing('PROCESSING', '처리중'),
  ready('READY', '준비됨'),
  failed('FAILED', '실패');

  const AudioFileStatus(this.value, this.displayName);
  final String value;
  final String displayName;
}

class BooksResponse {
  final String message;
  final List<Book> books;
  final PaginationInfo pagination;

  const BooksResponse({
    required this.message,
    required this.books,
    required this.pagination,
  });

  factory BooksResponse.fromJson(Map<String, dynamic> json) {
    return BooksResponse(
      message: json['message'] as String? ?? '도서 목록',
      books: (json['books'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(Book.fromJson)
          .toList(),
      pagination: PaginationInfo.fromJson(
        Map<String, dynamic>.from(json['pagination'] as Map),
      ),
    );
  }
}

class CategoriesResponse {
  final String message;
  final List<Category> categories;

  const CategoriesResponse({
    required this.message,
    required this.categories,
  });

  factory CategoriesResponse.fromJson(Map<String, dynamic> json) {
    return CategoriesResponse(
      message: json['message'] as String,
      categories: (json['categories'] as List)
          .map((e) => Category.fromJson(e))
          .toList(),
    );
  }
}

class BookmarksResponse {
  final String message;
  final List<Bookmark> bookmarks;
  final PaginationInfo pagination;

  const BookmarksResponse({
    required this.message,
    required this.bookmarks,
    required this.pagination,
  });

  factory BookmarksResponse.fromJson(Map<String, dynamic> json) {
    return BookmarksResponse(
      message: json['message'] as String? ?? '북마크 목록',
      bookmarks: (json['bookmarks'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(Bookmark.fromJson)
          .toList(),
      pagination: PaginationInfo.fromJson(
        Map<String, dynamic>.from(json['pagination'] as Map),
      ),
    );
  }
}

class PaginationInfo {
  final int page;
  final int limit;
  final int total;
  final int totalPages;
  final bool hasNext;

  const PaginationInfo({
    required this.page,
    required this.limit,
    required this.total,
    required this.totalPages,
    required this.hasNext,
  });

  factory PaginationInfo.fromJson(Map<String, dynamic> json) {
    final page = json['page'] as int? ?? 1;
    final limit = json['limit'] as int? ?? json['size'] as int? ?? 10;
    final total = json['total'] as int? ?? 0;
    final totalPages = json['totalPages'] as int? ??
        (limit <= 0 ? 1 : (total / limit).ceil());
    final hasNext = json['hasNext'] as bool? ??
        json['has_next'] as bool? ??
        (json['nextPage'] != null && json['nextPage'] != page);

    return PaginationInfo(
      page: page,
      limit: limit,
      total: total,
      totalPages: totalPages,
      hasNext: hasNext,
    );
  }

  bool get hasPrevious => page > 1;
}