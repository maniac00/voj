'use client'

import React, { useState, useEffect } from 'react'
import { usePlaybackState, usePlaybackHistory, PlaybackHistory } from '@/hooks/use-playback-state'
import { useNotification } from '@/contexts/notification-context'

interface PlaybackStateManagerProps {
  bookId: string
  chapterId?: string
  onResumePlayback?: (chapterId: string, position: number) => void
  className?: string
}

export function PlaybackStateManager({
  bookId,
  chapterId,
  onResumePlayback,
  className = ''
}: PlaybackStateManagerProps) {
  const { success, info } = useNotification()
  const [showHistory, setShowHistory] = useState(false)
  const [showBookmarks, setShowBookmarks] = useState(false)

  const {
    history,
    getRecentlyPlayed,
    getCompletedChapters,
    getInProgressChapters,
    removeFromHistory,
    clearHistory
  } = usePlaybackHistory(bookId)

  const recentlyPlayed = getRecentlyPlayed(5)
  const inProgress = getInProgressChapters()
  const completed = getCompletedChapters()

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = diffMs / (1000 * 60 * 60)
    
    if (diffHours < 1) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60))
      return `${diffMinutes}분 전`
    } else if (diffHours < 24) {
      return `${Math.floor(diffHours)}시간 전`
    } else {
      return date.toLocaleDateString('ko-KR')
    }
  }

  const handleResumeFromHistory = (record: PlaybackHistory) => {
    onResumePlayback?.(record.chapterId, record.currentTime)
    info(`${record.chapterTitle} ${formatTime(record.currentTime)} 위치에서 재생을 재개합니다.`)
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 95) return 'bg-green-500'
    if (percentage >= 50) return 'bg-blue-500'
    if (percentage >= 25) return 'bg-yellow-500'
    return 'bg-gray-500'
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">재생 기록</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`text-sm px-3 py-1 rounded ${
                showHistory ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
              }`}
            >
              기록 보기
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 진행 중인 챕터 */}
        {inProgress.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">이어서 듣기</h4>
            <div className="space-y-2">
              {inProgress.slice(0, 3).map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg cursor-pointer hover:bg-blue-100"
                  onClick={() => handleResumeFromHistory(record)}
                >
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-medium text-gray-900 truncate">
                      {record.chapterTitle}
                    </h5>
                    <div className="flex items-center space-x-2 mt-1">
                      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                        <div 
                          className={`h-1.5 rounded-full ${getProgressColor(record.completedPercentage)}`}
                          style={{ width: `${record.completedPercentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">
                        {Math.round(record.completedPercentage)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatTime(record.currentTime)} / {formatTime(record.duration)} • {formatDate(record.playedAt)}
                    </p>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleResumeFromHistory(record)
                    }}
                    className="ml-3 p-2 text-blue-600 hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                    aria-label={`${record.chapterTitle} 이어서 재생`}
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 최근 재생 */}
        {recentlyPlayed.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">최근 재생</h4>
            <div className="space-y-1">
              {recentlyPlayed.map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer"
                  onClick={() => handleResumeFromHistory(record)}
                >
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm text-gray-900 truncate">
                      {record.chapterTitle}
                    </h5>
                    <p className="text-xs text-gray-500">
                      {formatTime(record.currentTime)} • {formatDate(record.playedAt)}
                    </p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      record.completedPercentage >= 95 
                        ? 'bg-green-100 text-green-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {Math.round(record.completedPercentage)}%
                    </span>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        removeFromHistory(record.id)
                      }}
                      className="text-gray-400 hover:text-gray-600 focus:outline-none"
                      aria-label="기록 삭제"
                    >
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 완료된 챕터 */}
        {completed.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              완료된 챕터 ({completed.length}개)
            </h4>
            <div className="text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                <span>총 {Math.floor(completed.reduce((sum, r) => sum + r.duration, 0) / 60)}분 청취 완료</span>
              </div>
            </div>
          </div>
        )}

        {/* 전체 기록 보기 */}
        {showHistory && history.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-700">전체 재생 기록</h4>
              <button
                onClick={() => {
                  if (confirm('모든 재생 기록을 삭제하시겠습니까?')) {
                    clearHistory()
                    success('재생 기록이 삭제되었습니다.')
                  }
                }}
                className="text-xs text-red-600 hover:text-red-800"
              >
                전체 삭제
              </button>
            </div>
            
            <div className="max-h-48 overflow-y-auto space-y-1">
              {history.map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-2 text-sm hover:bg-gray-50 rounded"
                >
                  <div className="flex-1 min-w-0">
                    <div className="truncate">{record.chapterTitle}</div>
                    <div className="text-xs text-gray-500">
                      {formatTime(record.currentTime)} • {formatDate(record.playedAt)}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-600">
                      {Math.round(record.completedPercentage)}%
                    </span>
                    <button
                      onClick={() => handleResumeFromHistory(record)}
                      className="text-blue-600 hover:text-blue-800 focus:outline-none"
                      aria-label="재생"
                    >
                      ▶️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 빈 상태 */}
        {history.length === 0 && (
          <div className="text-center py-6 text-gray-500">
            <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">아직 재생 기록이 없습니다.</p>
            <p className="text-xs text-gray-400 mt-1">
              오디오를 재생하면 여기에 기록이 표시됩니다.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

interface ResumePlaybackPromptProps {
  chapterId: string
  chapterTitle: string
  savedPosition: number
  duration: number
  onResume: () => void
  onStartOver: () => void
  onDismiss: () => void
}

export function ResumePlaybackPrompt({
  chapterId,
  chapterTitle,
  savedPosition,
  duration,
  onResume,
  onStartOver,
  onDismiss
}: ResumePlaybackPromptProps) {
  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const progressPercentage = (savedPosition / duration) * 100

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <div className="flex items-center mb-4">
            <svg className="h-6 w-6 text-blue-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900">재생 이어하기</h3>
          </div>

          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              {chapterTitle}
            </h4>
            
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>저장된 위치</span>
                <span>{formatTime(savedPosition)} / {formatTime(duration)}</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              
              <div className="text-xs text-gray-500 mt-1 text-center">
                {Math.round(progressPercentage)}% 재생됨
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-3">
            <button
              onClick={onStartOver}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              처음부터
            </button>
            
            <button
              onClick={onResume}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              이어서 재생
            </button>
            
            <button
              onClick={onDismiss}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              취소
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

interface PlaybackStatsProps {
  bookId: string
  className?: string
}

export function PlaybackStats({ bookId, className = '' }: PlaybackStatsProps) {
  const { history, getCompletedChapters, getInProgressChapters } = usePlaybackHistory(bookId)
  
  const completed = getCompletedChapters()
  const inProgress = getInProgressChapters()
  
  const totalListenTime = history.reduce((sum, record) => {
    return sum + (record.duration * (record.completedPercentage / 100))
  }, 0)

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}시간 ${minutes}분`
    } else {
      return `${minutes}분`
    }
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">청취 통계</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{completed.length}</div>
          <div className="text-sm text-gray-600">완료한 챕터</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{inProgress.length}</div>
          <div className="text-sm text-gray-600">진행 중인 챕터</div>
        </div>
        
        <div className="text-center col-span-2">
          <div className="text-2xl font-bold text-gray-900">{formatDuration(totalListenTime)}</div>
          <div className="text-sm text-gray-600">총 청취 시간</div>
        </div>
      </div>

      {history.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            마지막 활동: {formatDate(new Date(Math.max(...history.map(h => h.playedAt.getTime()))))}
          </div>
        </div>
      )}
    </div>
  )

  function formatDate(date: Date) {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = diffMs / (1000 * 60 * 60)
    
    if (diffHours < 1) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60))
      return `${diffMinutes}분 전`
    } else if (diffHours < 24) {
      return `${Math.floor(diffHours)}시간 전`
    } else {
      return date.toLocaleDateString('ko-KR')
    }
  }
}
