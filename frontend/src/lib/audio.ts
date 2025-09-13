const API_BASE = process.env.NEXT_PUBLIC_API_BASE || `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1`

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
}

export async function fetchJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const res = await fetch(input, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
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


