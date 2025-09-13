'use client'

import React, { useState } from 'react'
import { ChapterDto } from '@/lib/audio'
import { MiniAudioPlayer } from '@/components/audio/audio-player'

interface QuickPlayerProps {
  chapter: ChapterDto
  onGetStreamingUrl: (chapterId: string) => Promise<string>
  className?: string
}

export function QuickPlayer({ chapter, onGetStreamingUrl, className = '' }: QuickPlayerProps) {
  const [streamingUrl, setStreamingUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handlePlay = async () => {
    if (streamingUrl) {
      // 이미 URL이 있으면 바로 재생
      return
    }

    setLoading(true)
    setError(null)

    try {
      const url = await onGetStreamingUrl(chapter.chapter_id)
      setStreamingUrl(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : '스트리밍 URL 생성 실패')
    } finally {
      setLoading(false)
    }
  }

  if (chapter.status !== 'ready') {
    return (
      <div className={`inline-flex items-center space-x-2 ${className}`}>
        <div className="p-1 text-gray-400 cursor-not-allowed" title="아직 준비되지 않음">
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
        </div>
        <span className="text-xs text-gray-500">처리 중</span>
      </div>
    )
  }

  if (loading) {
    return (
      <div className={`inline-flex items-center space-x-2 ${className}`}>
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span className="text-xs text-gray-500">로딩 중...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`inline-flex items-center space-x-2 ${className}`}>
        <div className="p-1 text-red-500" title={error}>
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <button
          onClick={handlePlay}
          className="text-xs text-blue-600 hover:text-blue-800"
        >
          재시도
        </button>
      </div>
    )
  }

  return (
    <div className={className}>
      <MiniAudioPlayer
        src={streamingUrl || ''}
        title={chapter.title}
        onPlay={handlePlay}
      />
    </div>
  )
}

interface PlaylistPlayerProps {
  chapters: ChapterDto[]
  currentChapterId?: string
  onGetStreamingUrl: (chapterId: string) => Promise<string>
  onChapterChange?: (chapterId: string) => void
  autoAdvance?: boolean
  className?: string
}

export function PlaylistPlayer({
  chapters,
  currentChapterId,
  onGetStreamingUrl,
  onChapterChange,
  autoAdvance = true,
  className = ''
}: PlaylistPlayerProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [streamingUrls, setStreamingUrls] = useState<Map<string, string>>(new Map())

  const readyChapters = chapters.filter(c => c.status === 'ready').sort((a, b) => a.chapter_number - b.chapter_number)
  const currentChapter = readyChapters[currentIndex]

  const handleNext = () => {
    if (currentIndex < readyChapters.length - 1) {
      const nextIndex = currentIndex + 1
      setCurrentIndex(nextIndex)
      onChapterChange?.(readyChapters[nextIndex].chapter_id)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1
      setCurrentIndex(prevIndex)
      onChapterChange?.(readyChapters[prevIndex].chapter_id)
    }
  }

  const handleChapterSelect = (chapterId: string) => {
    const index = readyChapters.findIndex(c => c.chapter_id === chapterId)
    if (index !== -1) {
      setCurrentIndex(index)
      onChapterChange?.(chapterId)
    }
  }

  const getStreamingUrl = async (chapterId: string) => {
    // 캐시된 URL이 있으면 사용
    if (streamingUrls.has(chapterId)) {
      return streamingUrls.get(chapterId)!
    }

    // 새로 URL 생성
    const url = await onGetStreamingUrl(chapterId)
    setStreamingUrls(prev => new Map(prev).set(chapterId, url))
    return url
  }

  if (readyChapters.length === 0) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 text-center ${className}`}>
        <p className="text-sm text-gray-600">재생 가능한 챕터가 없습니다.</p>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">플레이리스트</h3>
          <span className="text-sm text-gray-600">
            {currentIndex + 1} / {readyChapters.length}
          </span>
        </div>
      </div>

      <div className="p-4">
        {/* 현재 챕터 정보 */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-1">
            {currentChapter.title}
          </h4>
          <p className="text-xs text-gray-500">
            챕터 {currentChapter.chapter_number} • {Math.floor(currentChapter.duration / 60)}분
          </p>
        </div>

        {/* 플레이리스트 컨트롤 */}
        <div className="flex items-center justify-center space-x-3 mb-4">
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className="p-2 text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-black rounded"
            aria-label="이전 챕터"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <QuickPlayer
            chapter={currentChapter}
            onGetStreamingUrl={getStreamingUrl}
          />

          <button
            onClick={handleNext}
            disabled={currentIndex === readyChapters.length - 1}
            className="p-2 text-gray-600 hover:text-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-black rounded"
            aria-label="다음 챕터"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* 챕터 목록 */}
        <div className="max-h-40 overflow-y-auto">
          <div className="space-y-1">
            {readyChapters.map((chapter, index) => (
              <button
                key={chapter.chapter_id}
                onClick={() => handleChapterSelect(chapter.chapter_id)}
                className={`w-full text-left px-3 py-2 rounded text-sm ${
                  index === currentIndex
                    ? 'bg-blue-100 text-blue-900'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate">
                    {chapter.chapter_number}. {chapter.title}
                  </span>
                  <span className="text-xs text-gray-500 ml-2">
                    {Math.floor(chapter.duration / 60)}분
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
