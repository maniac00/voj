'use client'

import React, { useState } from 'react'
import { useParams } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { uploadAudio } from '@/lib/upload'

type Item = { name: string; progress: number; status: 'queued' | 'uploading' | 'done' | 'error' }

export default function BookAudiosPage() {
  const params = useParams()
  const bookId = String(params?.bookId || '')
  const [items, setItems] = useState<Item[]>([])

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
    </main>
  )
}


