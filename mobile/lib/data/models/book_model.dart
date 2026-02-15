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
  final List<AudioChapter> chapters;
  final int chapterCount;
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
    this.chapters = const [],
    this.chapterCount = 0,
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
    final chapterCountRaw = json['_count']?['chapters'] ?? json['chapterCount'] ?? json['total_chapters'];
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
      chapters: json['chapters'] != null
          ? (json['chapters'] as List)
              .whereType<Map<String, dynamic>>()
              .map(AudioChapter.fromJson)
              .toList()
          : const [],
      chapterCount: _parseInt(chapterCountRaw),
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
      'chapterCount': chapterCount,
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
    List<AudioChapter>? chapters,
    int? chapterCount,
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
      chapters: chapters ?? this.chapters,
      chapterCount: chapterCount ?? this.chapterCount,
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

class AudioChapter {
  final String id;
  final String bookId;
  final String title;
  final String fileName;
  final String? streamingUrl;
  final int? duration;
  final int chapterNumber;
  final AudioChapterStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? statusLabel;
  final int? fileSize;
  final String? contentPath;

  const AudioChapter({
    required this.id,
    required this.bookId,
    required this.title,
    required this.fileName,
    this.streamingUrl,
    this.duration,
    required this.chapterNumber,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.statusLabel,
    this.fileSize,
    this.contentPath,
  });

  /// 표시용 이름: 제목이 있으면 제목, 없으면 파일명
  String get displayName => title.isNotEmpty ? title : fileName;

  factory AudioChapter.fromJson(Map<String, dynamic> json) {
    return AudioChapter(
      id: json['chapter_id'] as String? ?? json['id'] as String? ?? '',
      bookId: json['book_id'] as String? ?? json['bookId'] as String? ?? '',
      title: json['title'] as String? ?? json['chapter_title'] as String? ?? '',
      fileName: json['file_name'] as String? ?? json['fileName'] as String? ?? '',
      streamingUrl: json['streaming_url'] as String?,
      duration: json['duration'] as int? ?? json['duration_seconds'] as int?,
      chapterNumber: json['chapter_number'] as int? ?? json['sequence'] as int? ?? 0,
      status: AudioChapterStatus.values.firstWhere(
        (e) => e.name == (json['status'] as String? ?? '').toLowerCase(),
        orElse: () => AudioChapterStatus.processing,
      ),
      createdAt: _parseDateTime(json['createdAt'] ?? json['created_at']) ?? DateTime.now(),
      updatedAt: _parseDateTime(json['updatedAt'] ?? json['updated_at']) ?? DateTime.now(),
      statusLabel: json['status_label'] as String? ?? json['statusDisplay'] as String?,
      fileSize: json['file_size'] as int? ?? json['fileSize'] as int?,
      contentPath: json['content_path'] as String? ?? json['contentPath'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'bookId': bookId,
      'fileName': fileName,
      'streamingUrl': streamingUrl,
      'duration': duration,
      'chapterNumber': chapterNumber,
      'status': status.name,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
      'statusLabel': statusLabel,
      'fileSize': fileSize,
      'contentPath': contentPath,
    };
  }

  String get durationText {
    if (duration == null) {
      return '--:--';
    }
    final minutes = duration! ~/ 60;
    final seconds = duration! % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
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

enum AudioChapterStatus {
  processing('PROCESSING', '처리중'),
  ready('READY', '준비됨'),
  failed('FAILED', '실패');

  const AudioChapterStatus(this.value, this.displayName);
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