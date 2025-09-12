'use client'

import React, { useState } from 'react'
import { createBook } from '@/lib/api'
import { useRouter } from 'next/navigation'

export default function NewBookPage() {
  const router = useRouter()
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [publisher, setPublisher] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await createBook({ title, author, publisher })
      router.push('/books')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="p-6 max-w-xl">
      <h1 className="text-xl font-semibold mb-4">새 책 등록</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
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
        <button disabled={submitting} className="rounded bg-black px-4 py-2 text-white disabled:opacity-50">등록</button>
      </form>
    </main>
  )
}


