class User {
  final String id;
  final String name;
  final String? email;
  final UserStatus status;
  final DateTime? createdAt;
  final DateTime? lastLoginAt;
  final String? scope;

  const User({
    required this.id,
    required this.name,
    this.email,
    this.status = UserStatus.pending,
    this.createdAt,
    this.lastLoginAt,
    this.scope,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    // sub/username 키가 있어도 status 필드가 함께 있으면 일반 파싱 사용
    if ((json.containsKey('sub') || json.containsKey('username')) &&
        !json.containsKey('status')) {
      return User._fromAuthIdentity(json);
    }

    return User(
      id: (json['id'] ?? json['sub'] ?? json['user_id'] ?? '') as String,
      name: (json['name'] ?? json['username'] ?? '') as String,
      email: json['email'] as String?,
      status: _parseStatus(json['status']),
      createdAt: json['createdAt'] != null
          ? DateTime.parse(json['createdAt'] as String)
          : null,
      lastLoginAt: json['lastLoginAt'] != null
          ? DateTime.parse(json['lastLoginAt'] as String)
          : null,
      scope: json['scope'] as String?,
    );
  }

  static UserStatus _parseStatus(dynamic value) {
    if (value is String) {
      return UserStatus.values.firstWhere(
        (e) => e.name == value || e.value == value,
        orElse: () => UserStatus.pending,
      );
    }
    return UserStatus.pending;
  }

  factory User._fromAuthIdentity(Map<String, dynamic> json) {
    final scope = json['scope'] as String?;
    return User(
      id: (json['sub'] ?? json['id'] ?? '') as String,
      name: (json['username'] ?? json['name'] ?? '') as String,
      email: json['email'] as String?,
      status: _parseStatus(json['status']),
      scope: scope,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'status': status.name,
      'createdAt': createdAt?.toIso8601String(),
      'lastLoginAt': lastLoginAt?.toIso8601String(),
      if (scope != null) 'scope': scope,
    };
  }

  Map<String, dynamic> toStorageJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'status': status.name,
      if (scope != null) 'scope': scope,
      'createdAt': createdAt?.toIso8601String(),
      'lastLoginAt': lastLoginAt?.toIso8601String(),
    };
  }

  User copyWith({
    String? id,
    String? name,
    String? email,
    UserStatus? status,
    DateTime? createdAt,
    DateTime? lastLoginAt,
    String? scope,
  }) {
    return User(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      lastLoginAt: lastLoginAt ?? this.lastLoginAt,
      scope: scope ?? this.scope,
    );
  }
}

enum UserStatus {
  pending('PENDING', '승인 대기'),
  approved('APPROVED', '승인됨'),
  suspended('SUSPENDED', '정지됨');

  const UserStatus(this.value, this.displayName);
  final String value;
  final String displayName;
}

class AuthSession {
  final String accessToken;
  final String tokenType;
  final DateTime issuedAt;
  final DateTime expiresAt;
  final String? scope;
  final String? username;

  const AuthSession({
    required this.accessToken,
    required this.tokenType,
    required this.issuedAt,
    required this.expiresAt,
    this.scope,
    this.username,
  });

  bool get isExpired => DateTime.now().toUtc().isAfter(expiresAt);
  bool get isValid => !isExpired;

  Duration? get remainingDuration {
    if (isExpired) return Duration.zero;
    return expiresAt.difference(DateTime.now().toUtc());
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'token_type': tokenType,
      'issued_at': issuedAt.toIso8601String(),
      'expires_at': expiresAt.toIso8601String(),
      if (scope != null) 'scope': scope,
      if (username != null) 'username': username,
    };
  }

  AuthSession copyWith({
    String? accessToken,
    String? tokenType,
    DateTime? issuedAt,
    DateTime? expiresAt,
    String? scope,
    String? username,
  }) {
    return AuthSession(
      accessToken: accessToken ?? this.accessToken,
      tokenType: tokenType ?? this.tokenType,
      issuedAt: issuedAt ?? this.issuedAt,
      expiresAt: expiresAt ?? this.expiresAt,
      scope: scope ?? this.scope,
      username: username ?? this.username,
    );
  }

  factory AuthSession.fromLoginJson(
    Map<String, dynamic> json, {
    DateTime? issuedAt,
  }) {
    final accessToken = json['access_token'] as String?;
    if (accessToken == null || accessToken.isEmpty) {
      throw const FormatException('로그인 응답에 access_token이 없습니다.');
    }

    final expiresInRaw = json['expires_in'];
    final expiresInSeconds = expiresInRaw is int
        ? expiresInRaw
        : int.tryParse(expiresInRaw?.toString() ?? '') ?? 0;

    final issued = (issuedAt ?? DateTime.now()).toUtc();
    final expiresAt = issued.add(Duration(seconds: expiresInSeconds));

    return AuthSession(
      accessToken: accessToken,
      tokenType: (json['token_type'] as String?)?.toLowerCase() ?? 'bearer',
      issuedAt: issued,
      expiresAt: expiresAt,
      scope: json['scope'] as String?,
      username: json['username'] as String?,
    );
  }

  factory AuthSession.fromStorageJson(Map<String, dynamic> json) {
    final accessToken = json['access_token'] as String?;
    final expiresAtString = json['expires_at'] as String?;
    final issuedAtString = json['issued_at'] as String?;

    if (accessToken == null ||
        expiresAtString == null ||
        issuedAtString == null) {
      throw const FormatException('저장된 인증 세션 데이터가 올바르지 않습니다.');
    }

    return AuthSession(
      accessToken: accessToken,
      tokenType: (json['token_type'] as String?)?.toLowerCase() ?? 'bearer',
      issuedAt: DateTime.parse(issuedAtString).toUtc(),
      expiresAt: DateTime.parse(expiresAtString).toUtc(),
      scope: json['scope'] as String?,
      username: json['username'] as String?,
    );
  }
}

class AuthResponse {
  final String? message;
  final User? user;
  final AuthSession? session;

  const AuthResponse({this.message, this.user, this.session});

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      message: json['message'] as String?,
      user: json['user'] is Map<String, dynamic>
          ? User.fromJson(json['user'] as Map<String, dynamic>)
          : null,
      session: json['access_token'] != null
          ? AuthSession.fromLoginJson(json)
          : null,
    );
  }
}
