export type UploadProgressHandler = (loaded: number, total: number) => void

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || `${process.env.NEXT_PUBLIC_API_URL || ''}/api/v1`

export async function uploadAudio(
  bookId: string,
  file: File,
  onProgress?: UploadProgressHandler
): Promise<{ message: string } | any> {
  const url = `${API_BASE}/files/upload?book_id=${encodeURIComponent(bookId)}&file_type=uploads`
  const form = new FormData()
  form.append('file', file, file.name)

  // Use XHR for progress support
  const response = await new Promise<Response>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', url)
    xhr.onreadystatechange = () => {
      if (xhr.readyState === 4) {
        const resp = new Response(xhr.responseText, { status: xhr.status, statusText: xhr.statusText })
        resolve(resp)
      }
    }
    xhr.onerror = () => reject(new Error('Network error during upload'))
    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(e.loaded, e.total)
      }
    }
    xhr.send(form)
  })

  if (!response.ok) {
    const text = await response.text().catch(() => '')
    throw new Error(`Upload failed: ${response.status} ${response.statusText} ${text}`)
  }
  try {
    return await response.json()
  } catch {
    return { message: 'uploaded' }
  }
}


