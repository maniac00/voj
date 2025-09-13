'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { getChapters, reorderChapter, deleteChapter, type ChapterDto } from '@/lib/audio'
import { getBook, BookDto } from '@/lib/api'
import { FileUploadForm } from '@/components/audio/file-upload-form'
import { ChapterList, ChapterStats, ChapterSearch } from '@/components/audio/chapter-list'
import { useNotification } from '@/contexts/notification-context'
import { ErrorState, LoadingState } from '@/components/ui/error-state'

export default function BookAudiosPage() {
  const params = useParams()
  const bookId = String(params?.bookId || '')
  const [book, setBook] = useState<BookDto | null>(null)
  const [chapters, setChapters] = useState<ChapterDto[]>([])
  const [filteredChapters, setFilteredChapters] = useState<ChapterDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { success, error: showError } = useNotification()

  useEffect(() => {
    const loadData = async () => {
      if (!bookId) return

      try {
        // 책 정보와 챕터 목록을 병렬로 로드
        const [bookData, chaptersData] = await Promise.all([
          getBook(bookId),
          getChapters(bookId).catch(() => [])
        ])

        setBook(bookData)
        const sortedChapters = chaptersData.sort((a, b) => a.chapter_number - b.chapter_number)
        setChapters(sortedChapters)
        setFilteredChapters(sortedChapters)
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터를 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [bookId])

  const handleUploadComplete = (chapterId: string, fileName: string) => {
    // 챕터 목록 새로고침
    getChapters(bookId)
      .then(data => {
        const sortedChapters = data.sort((a, b) => a.chapter_number - b.chapter_number)
        setChapters(sortedChapters)
        setFilteredChapters(sortedChapters)
      })
      .catch(() => {
        showError('챕터 목록을 새로고침하는데 실패했습니다.')
      })
  }

  const handleChapterReorder = async (chapterId: string, direction: 'up' | 'down') => {
    const chapter = chapters.find(c => c.chapter_id === chapterId)
    if (!chapter) return

    try {
      const newNumber = direction === 'up' 
        ? Math.max(1, chapter.chapter_number - 1)
        : chapter.chapter_number + 1

      const updated = await reorderChapter(bookId, chapter.chapter_id, newNumber)
      
      const updatedChapters = chapters
        .map(x => x.chapter_id === chapter.chapter_id ? updated : x)
        .sort((a, b) => a.chapter_number - b.chapter_number)
      
      setChapters(updatedChapters)
      setFilteredChapters(updatedChapters)

    } catch (err) {
      throw err // ChapterList에서 에러 처리
    }
  }

  const handleChapterDelete = async (chapterId: string) => {
    try {
      await deleteChapter(bookId, chapterId)
      const updatedChapters = chapters.filter(c => c.chapter_id !== chapterId)
      setChapters(updatedChapters)
      setFilteredChapters(updatedChapters)
    } catch (err) {
      throw err // ChapterList에서 에러 처리
    }
  }

  const handleChapterPlay = (chapterId: string) => {
    // TODO: 오디오 재생 기능 (다음 태스크에서 구현)
    console.log(`Playing chapter: ${chapterId}`)
    showError('오디오 재생 기능은 다음 단계에서 구현됩니다.')
  }

  const handleChapterEdit = (chapterId: string) => {
    // TODO: 챕터 편집 기능
    console.log(`Editing chapter: ${chapterId}`)
    showError('챕터 편집 기능은 향후 구현 예정입니다.')
  }

  if (loading) {
    return <LoadingState message="책 정보와 챕터 목록을 불러오는 중..." />
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState
          title="데이터 로드 실패"
          message={error}
          showRetry={true}
          onRetry={() => window.location.reload()}
          showHome={true}
        />
      </div>
    )
  }

  if (!book) {
    return (
      <div className="p-6">
        <ErrorState
          title="책을 찾을 수 없습니다"
          message="요청하신 책이 존재하지 않거나 접근 권한이 없습니다."
          showHome={true}
        />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">오디오 파일 관리</h1>
            <p className="mt-1 text-sm text-gray-600">
              <strong>"{book.title}"</strong> - {book.author}
            </p>
          </div>
          <Link 
            href={`/books/${bookId}`}
            className="text-gray-600 hover:text-gray-900 text-sm"
          >
            ← 책 편집으로 돌아가기
          </Link>
        </div>
      </div>

      <div className="space-y-6">
        {/* 파일 업로드 */}
        <FileUploadForm
          bookId={bookId}
          onUploadComplete={handleUploadComplete}
          onUploadStart={(fileName) => {
            console.log(`Upload started: ${fileName}`)
          }}
        />

        {/* 챕터 통계 */}
        {chapters.length > 0 && (
          <ChapterStats chapters={chapters} />
        )}

        {/* 챕터 검색 및 필터 */}
        {chapters.length > 0 && (
          <ChapterSearch
            chapters={chapters}
            onFilter={setFilteredChapters}
          />
        )}

        {/* 챕터 목록 */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">챕터 목록</h2>
              <div className="text-sm text-gray-600">
                {filteredChapters.length !== chapters.length 
                  ? `${filteredChapters.length}개 표시 (전체 ${chapters.length}개)`
                  : `총 ${chapters.length}개 챕터`
                }
              </div>
            </div>
          </div>
          
          <div className="p-6">
            <ChapterList
              chapters={filteredChapters}
              onReorder={handleChapterReorder}
              onDelete={handleChapterDelete}
              onPlay={handleChapterPlay}
              onEdit={handleChapterEdit}
            />
          </div>
        </div>
      </div>
    </div>
  )
}


