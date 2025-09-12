const API_BASE = process.env.NEXT_PUBLIC_API_BASE || `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1`

export type BookDto = {
  book_id: string
  user_id: string
  title: string
  author: string
  publisher?: string | null
  status?: string
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

export async function getBooks(): Promise<BookDto[]> {
  return fetchJson<BookDto[]>(`${API_BASE}/books`)
}

export async function getBook(bookId: string): Promise<BookDto> {
  return fetchJson<BookDto>(`${API_BASE}/books/${bookId}`)
}

export async function createBook(payload: { title: string; author: string; publisher?: string }): Promise<BookDto> {
  return fetchJson<BookDto>(`${API_BASE}/books`, {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function updateBook(bookId: string, payload: Partial<{ title: string; author: string; publisher: string }>): Promise<BookDto> {
  return fetchJson<BookDto>(`${API_BASE}/books/${bookId}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deleteBook(bookId: string): Promise<{ message: string }> {
  return fetchJson<{ message: string }>(`${API_BASE}/books/${bookId}`, { method: 'DELETE' })
}


