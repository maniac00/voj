'use client'

import React, { useEffect, useState } from 'react'
import { deleteBook, getBook, updateBook } from '@/lib/api'
import { useParams, useRouter } from 'next/navigation'

export default function EditBookPage() {
  const params = useParams()
  const bookId = String(params?.bookId || '')
  const router = useRouter()
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [publisher, setPublisher] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const b = await getBook(bookId)
        setTitle(b.title)
        setAuthor(b.author)
        setPublisher(b.publisher || '')
      } finally {
        setLoading(false)
      }
    }
    if (bookId) load()
  }, [bookId])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await updateBook(bookId, { title, author, publisher })
      router.push('/books')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!confirm('정말 삭제하시겠습니까?')) return
    await deleteBook(bookId)
    router.push('/books')
  }

  if (loading) return <main className="p-6">로딩...</main>

  return (
    <main className="p-6 max-w-xl">
      <h1 className="text-xl font-semibold mb-4">책 편집</h1>
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">제목</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" required />
        </div>
        <div>
          <label className="block text-sm font-medium">저자</label>
          <input value={author} onChange={(e) => setAuthor(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" required />
        </div>
        <div>
          <label className="block text-sm font-medium">출판사</label>
          <input value={publisher} onChange={(e) => setPublisher(e.target.value)} className="mt-1 w-full rounded border px-3 py-2" />
        </div>
        <div className="flex gap-2">
          <button disabled={saving} className="rounded bg-black px-4 py-2 text-white disabled:opacity-50">저장</button>
          <button type="button" onClick={handleDelete} className="rounded bg-red-600 px-4 py-2 text-white">삭제</button>
        </div>
      </form>
    </main>
  )
}


