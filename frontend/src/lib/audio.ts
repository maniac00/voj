import { getAuthHeaders } from '@/lib/auth/simple-auth'

// 브라우저에서는 동일 출처 경로 사용
const API_BASE = typeof window !== 'undefined'
  ? ((process.env.NEXT_PUBLIC_API_BASE && !/^https?:/i.test(process.env.NEXT_PUBLIC_API_BASE))
      ? process.env.NEXT_PUBLIC_API_BASE
      : '/api/v1')
  : (process.env.NEXT_PUBLIC_API_BASE || `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1`)

export type ChapterDto = {
  chapter_id: string
  book_id: string
  chapter_number: number
  title: string
  description?: string | null
  file_name: string
  file_size: number
  duration: number
  status: string
  created_at?: string
  updated_at?: string
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

export async function getChapters(bookId: string): Promise<ChapterDto[]> {
  return fetchJson<ChapterDto[]>(`${API_BASE}/audio/${encodeURIComponent(bookId)}/chapters`)
}

export async function reorderChapter(bookId: string, chapterId: string, newNumber: number): Promise<ChapterDto> {
  return fetchJson<ChapterDto>(
    `${API_BASE}/audio/${encodeURIComponent(bookId)}/chapters/${encodeURIComponent(chapterId)}?new_number=${newNumber}`,
    { method: 'PUT' }
  )
}

export async function deleteChapter(bookId: string, chapterId: string): Promise<{ message: string }> {
  return fetchJson<{ message: string }>(
    `${API_BASE}/audio/${encodeURIComponent(bookId)}/chapters/${encodeURIComponent(chapterId)}`,
    { method: 'DELETE' }
  )
}

export type StreamUrlResponse = {
  streaming_url: string
  expires_at: string
  duration: number
}

export async function getStreamingUrlApi(bookId: string, chapterId: string): Promise<StreamUrlResponse> {
  return fetchJson<StreamUrlResponse>(
    `${API_BASE}/audio/${encodeURIComponent(bookId)}/chapters/${encodeURIComponent(chapterId)}/stream`
  )
}


