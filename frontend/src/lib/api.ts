import { getAuthHeaders } from '@/lib/auth/simple-auth'

// 브라우저에서는 항상 동일 출처 경로로 호출하여 Mixed Content를 방지
const API_BASE = typeof window !== 'undefined'
  ? ((process.env.NEXT_PUBLIC_API_BASE && !/^https?:/i.test(process.env.NEXT_PUBLIC_API_BASE))
      ? process.env.NEXT_PUBLIC_API_BASE
      : '/api/v1')
  : (process.env.NEXT_PUBLIC_API_BASE || `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1`)

export type BookDto = {
  book_id: string
  user_id: string
  title: string
  author: string
  publisher?: string | null
  description?: string | null
  genre?: string | null
  language?: string
  status?: string
  created_at?: string
  updated_at?: string
  total_chapters?: number
  total_duration?: number
}

export async function fetchJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const res = await fetch(input, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...(init?.headers || {})
    },
    cache: 'no-store'
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Request failed: ${res.status} ${res.statusText} ${text}`)
  }
  return (await res.json()) as T
}

export async function getBooks(): Promise<BookDto[]> {
  const data = await fetchJson<any>(`${API_BASE}/books`)
  if (Array.isArray(data)) return data as BookDto[]
  if (Array.isArray(data?.books)) return data.books as BookDto[]
  if (Array.isArray(data?.items)) return data.items as BookDto[]
  if (Array.isArray(data?.data?.books)) return data.data.books as BookDto[]
  if (Array.isArray(data?.data?.items)) return data.data.items as BookDto[]
  return []
}

export async function getBook(bookId: string): Promise<BookDto> {
  return fetchJson<BookDto>(`${API_BASE}/books/${bookId}`)
}

export interface CreateBookPayload {
  title: string
  author: string
  publisher?: string
  description?: string
  genre?: string
  language?: string
}

export async function createBook(payload: CreateBookPayload): Promise<BookDto> {
  return fetchJson<BookDto>(`${API_BASE}/books`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export type UpdateBookPayload = Partial<CreateBookPayload>

export async function updateBook(bookId: string, payload: UpdateBookPayload): Promise<BookDto> {
  return fetchJson<BookDto>(`${API_BASE}/books/${bookId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deleteBook(bookId: string): Promise<{ message: string }> {
  return fetchJson<{ message: string }>(`${API_BASE}/books/${bookId}`, { method: 'DELETE' })
}

// Health
export interface HealthDependencyInfo {
  status?: string
  [key: string]: any
}

export interface HealthDetailedResponse {
  status: string
  environment: string
  version: string
  dependencies: Record<string, HealthDependencyInfo>
}

export async function getHealthDetailed(): Promise<HealthDetailedResponse> {
  return fetchJson<HealthDetailedResponse>(`${API_BASE}/health/detailed`)
}


