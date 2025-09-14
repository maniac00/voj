'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { getBooks, type BookDto, getHealthDetailed, type HealthDetailedResponse } from '@/lib/api'
import { getChapters, type ChapterDto } from '@/lib/audio'
import { ErrorState, LoadingState } from '@/components/ui/error-state'

export default function AdminDashboardPage() {
  function StatCard({ label, value, ariaLabel }: { label: string; value: React.ReactNode; ariaLabel: string }) {
    return (
      <div
        className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus-within:ring-2 focus-within:ring-black/50"
        role="status"
        aria-live="polite"
        aria-label={ariaLabel}
      >
        <div className="text-sm text-gray-500">{label}</div>
        <div className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">{value}</div>
      </div>
    )
  }
  const [books, setBooks] = useState<BookDto[]>([])
  const [chapters, setChapters] = useState<number>(0)
  const [health, setHealth] = useState<HealthDetailedResponse | null>(null)
  const [recent, setRecent] = useState<Array<{ book: BookDto; chapter: ChapterDto }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    const load = async () => {
      try {
        const [bookList, healthResp] = await Promise.all([
          getBooks().catch(() => []),
          getHealthDetailed().catch(() => null as any)
        ])
        setBooks(bookList || [])
        setHealth(healthResp)

        // Count chapters across books (best-effort)
        let totalChapters = 0
        const recentList: Array<{ book: BookDto; chapter: ChapterDto }> = []
        if (bookList && bookList.length > 0) {
          for (const b of bookList.slice(0, 10)) {
            try {
              const cs: ChapterDto[] = await getChapters(b.book_id)
              totalChapters += cs.length
              cs.forEach((c) => recentList.push({ book: b, chapter: c }))
            } catch {
              // ignore
            }
          }
          // 최신순으로 최대 10개
          recentList.sort((a, b) => {
            const tA = Date.parse(a.chapter.updated_at || a.chapter.created_at || '1970-01-01')
            const tB = Date.parse(b.chapter.updated_at || b.chapter.created_at || '1970-01-01')
            return tB - tA
          })
          setRecent(recentList.slice(0, 10))
        }
        setChapters(totalChapters)
      } catch (e) {
        setError(e instanceof Error ? e.message : '대시보드 로드 실패')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <LoadingState message="대시보드 데이터를 불러오는 중..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState
          title="대시보드 로드 실패"
          message={error}
          showRetry
          onRetry={() => window.location.reload()}
          showHome
        />
      </div>
    )
  }

  const dep = (k: string) => health?.dependencies?.[k]?.status || 'unknown'

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-6" aria-labelledby="dashboard-title">
      <div className="flex items-center justify-between">
        <h1 id="dashboard-title" className="text-2xl font-semibold text-gray-900">대시보드</h1>
        <Link href="/books" className="text-sm text-gray-600 hover:text-gray-900">책 목록으로</Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <StatCard label="총 책 수" value={books.length} ariaLabel="총 책 수" />
        <StatCard label="대략적 총 챕터 수" value={chapters} ariaLabel="총 챕터 수" />
        <StatCard label="시스템 상태" value={(health?.status || 'unknown').toUpperCase()} ariaLabel="시스템 상태" />
      </div>

      <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm" aria-labelledby="deps-section">
        <h2 id="deps-section" className="text-lg font-medium text-gray-900 mb-4">종속성 상태</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="rounded-lg border p-4">
            <div className="text-gray-500">DynamoDB</div>
            <div className="font-medium">{dep('dynamodb')}</div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="text-gray-500">Local Storage</div>
            <div className="font-medium">{dep('local_storage')}</div>
          </div>
          <div className="rounded-lg border p-4">
            <div className="text-gray-500">Environment</div>
            <div className="font-medium">{dep('environment')}</div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm" aria-labelledby="recent-section">
        <h2 id="recent-section" className="text-lg font-medium text-gray-900 mb-4">최근 업로드/활동</h2>
        {recent.length === 0 ? (
          <div className="text-sm text-gray-500" role="note">최근 항목이 없습니다.</div>
        ) : (
          <ul className="divide-y divide-gray-100 text-sm" aria-label="최근 업로드 리스트">
            {recent.map(({ book, chapter }) => (
              <li key={`${book.book_id}-${chapter.chapter_id}`} className="py-2 flex items-center justify-between">
                <div className="min-w-0">
                  <div className="truncate font-medium text-gray-900">{chapter.title}</div>
                  <div className="truncate text-gray-500">
                    {book.title} • 챕터 {chapter.chapter_number} • {(chapter.file_size / (1024*1024)).toFixed(1)}MB
                  </div>
                </div>
                <div className="text-gray-500 ml-4 whitespace-nowrap">
                  {new Date(chapter.updated_at || chapter.created_at || Date.now()).toLocaleString()}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
