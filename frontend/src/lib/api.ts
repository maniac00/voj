import { getAuthHeaders } from "@/lib/auth/simple-auth";
import { apiBase } from "@/lib/config";

export type BookDto = {
  book_id: string;
  user_id: string;
  title: string;
  author: string;
  publisher?: string | null;
  description?: string | null;
  genre?: string | null;
  language?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  total_chapters?: number;
  total_duration?: number;
  cover_image_url?: string | null;
};

const DEFAULT_TIMEOUT_MS = 30_000;

export async function fetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const res = await fetch(input, {
      ...init,
      signal: init?.signal ?? controller.signal,
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        ...getAuthHeaders(),
        ...(init?.headers || {}),
      },
      cache: "no-store",
    });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`Request failed: ${res.status} ${res.statusText} ${text}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function getBooks(): Promise<BookDto[]> {
  const data = await fetchJson<any>(`${apiBase()}/books`);
  if (Array.isArray(data)) return data as BookDto[];
  if (Array.isArray(data?.books)) return data.books as BookDto[];
  if (Array.isArray(data?.items)) return data.items as BookDto[];
  if (Array.isArray(data?.data?.books)) return data.data.books as BookDto[];
  if (Array.isArray(data?.data?.items)) return data.data.items as BookDto[];
  return [];
}

export async function getBook(bookId: string): Promise<BookDto> {
  return fetchJson<BookDto>(`${apiBase()}/books/${bookId}`);
}

export interface CreateBookPayload {
  title: string;
  author: string;
  publisher?: string;
  description?: string;
  genre?: string;
  language?: string;
}

export async function createBook(payload: CreateBookPayload): Promise<BookDto> {
  return fetchJson<BookDto>(`${apiBase()}/books`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type UpdateBookPayload = Partial<CreateBookPayload> & {
  cover_image_url?: string | null;
  cover_image_key?: string | null;
};

export async function updateBook(
  bookId: string,
  payload: UpdateBookPayload,
): Promise<BookDto> {
  return fetchJson<BookDto>(`${apiBase()}/books/${bookId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteBook(bookId: string): Promise<{ message: string }> {
  return fetchJson<{ message: string }>(`${apiBase()}/books/${bookId}`, {
    method: "DELETE",
  });
}

// Cover image upload
export interface FileUploadResponse {
  success: boolean;
  file_id: string;
  key: string;
  size: number;
  content_type: string;
  url: string | null;
  message: string;
}

export async function uploadBookCover(
  bookId: string,
  userId: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<BookDto> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${apiBase()}/files/upload?user_id=${encodeURIComponent(userId)}&book_id=${encodeURIComponent(bookId)}&file_type=cover`;

  const uploadResult = await new Promise<FileUploadResponse>(
    (resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", url);

      const cookieMatch = document.cookie
        .split("; ")
        .find((row) => row.startsWith("voj_access_token="));
      const token = cookieMatch
        ? cookieMatch.substring(cookieMatch.indexOf("=") + 1)
        : undefined;
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
        }
      };

      xhr.onerror = () => reject(new Error("Upload failed: network error"));
      xhr.send(formData);
    },
  );

  // Update book with cover image info
  // 항상 API 파일 엔드포인트 경로를 저장 (모바일 앱에서도 사용 가능하도록)
  const coverUrl = `/api/v1/files/${uploadResult.key}`;
  return updateBook(bookId, {
    cover_image_url: coverUrl,
    cover_image_key: uploadResult.key,
  });
}

// Health
export interface HealthDependencyInfo {
  status?: string;
  [key: string]: any;
}

export interface HealthDetailedResponse {
  status: string;
  environment: string;
  version: string;
  dependencies: Record<string, HealthDependencyInfo>;
}

export async function getHealthDetailed(): Promise<HealthDetailedResponse> {
  return fetchJson<HealthDetailedResponse>(`${apiBase()}/health/detailed`);
}

// Analytics
export interface AnalyticsOverview {
  installations: {
    total: number;
    active: number;
  };
  active_users: {
    daily: number;
    weekly: number;
    monthly: number;
  };
  playback: {
    total_seconds: number;
    total_sessions: number;
    avg_session_seconds: number;
    completed_sessions: number;
  };
  daily_active_users: Array<{ date: string; users: number }>;
  popular_books: Array<{
    book_id: string;
    title: string;
    total_seconds: number;
    session_count: number;
  }>;
}

export interface UserStat {
  user_id: number;
  display_name: string;
  email: string;
  status: string;
  total_play_seconds: number;
  session_count: number;
  last_activity: string | null;
  completed_books: number;
  device_model: string | null;
  app_version: string | null;
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return fetchJson<AnalyticsOverview>(`${apiBase()}/analytics/admin/overview`);
}

export async function getAnalyticsUserStats(): Promise<{ users: UserStat[] }> {
  return fetchJson<{ users: UserStat[] }>(
    `${apiBase()}/analytics/admin/user-stats`,
  );
}
