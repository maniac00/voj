'use client'

import React, { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { uploadAudio } from '@/lib/upload'
import { getChapters, reorderChapter, type ChapterDto } from '@/lib/audio'

type Item = { name: string; progress: number; status: 'queued' | 'uploading' | 'done' | 'error' }

export default function BookAudiosPage() {
  const params = useParams()
  const bookId = String(params?.bookId || '')
  const [items, setItems] = useState<Item[]>([])
  const [chapters, setChapters] = useState<ChapterDto[]>([])

  useEffect(() => {
    async function load() {
      const data = await getChapters(bookId).catch(() => [])
      setChapters(data.sort((a, b) => a.chapter_number - b.chapter_number))
    }
    if (bookId) void load()
  }, [bookId])

  const onDrop = (acceptedFiles: File[]) => {
    acceptedFiles.forEach(async (file) => {
      setItems((prev) => [...prev, { name: file.name, progress: 0, status: 'queued' }])
      try {
        setItems((prev) => prev.map((i) => (i.name === file.name ? { ...i, status: 'uploading' } : i)))
        await uploadAudio(bookId, file, (loaded, total) => {
          const progress = Math.round((loaded / total) * 100)
          setItems((prev) => prev.map((i) => (i.name === file.name ? { ...i, progress } : i)))
        })
        setItems((prev) => prev.map((i) => (i.name === file.name ? { ...i, status: 'done', progress: 100 } : i)))
      } catch (e) {
        setItems((prev) => prev.map((i) => (i.name === file.name ? { ...i, status: 'error' } : i)))
      }
    })
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  return (
    <main className="p-6">
      <h1 className="text-xl font-semibold mb-4">오디오 업로드</h1>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded p-8 text-center ${isDragActive ? 'bg-slate-50' : 'bg-white'}`}
      >
        <input {...getInputProps()} />
        <p>여기로 파일을 드래그하거나 클릭하여 선택하세요 (WAV/MP3/M4A)</p>
      </div>

      <ul className="mt-6 space-y-2">
        {items.map((i) => (
          <li key={i.name} className="border rounded p-3">
            <div className="flex items-center justify-between">
              <span>{i.name}</span>
              <span className="text-sm text-slate-600">{i.status}</span>
            </div>
            <div className="mt-2 h-2 w-full rounded bg-slate-200">
              <div className="h-2 rounded bg-black" style={{ width: `${i.progress}%` }} />
            </div>
          </li>
        ))}
      </ul>

      <h2 className="text-lg font-semibold mt-8 mb-2">챕터 정렬</h2>
      <ul className="space-y-2">
        {chapters.map((c, idx) => (
          <li key={c.chapter_id} className="border rounded p-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="w-10 text-right">{c.chapter_number}</span>
              <span>{c.title}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                className="rounded border px-2 py-1"
                disabled={idx === 0}
                onClick={async () => {
                  const newNum = Math.max(1, c.chapter_number - 1)
                  const updated = await reorderChapter(bookId, c.chapter_id, newNum)
                  setChapters((prev) =>
                    prev
                      .map((x) => (x.chapter_id === c.chapter_id ? updated : x))
                      .sort((a, b) => a.chapter_number - b.chapter_number)
                  )
                }}
              >
                ↑
              </button>
              <button
                className="rounded border px-2 py-1"
                disabled={idx === chapters.length - 1}
                onClick={async () => {
                  const newNum = c.chapter_number + 1
                  const updated = await reorderChapter(bookId, c.chapter_id, newNum)
                  setChapters((prev) =>
                    prev
                      .map((x) => (x.chapter_id === c.chapter_id ? updated : x))
                      .sort((a, b) => a.chapter_number - b.chapter_number)
                  )
                }}
              >
                ↓
              </button>
            </div>
          </li>
        ))}
      </ul>
    </main>
  )
}


