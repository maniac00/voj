'use client'

import React, { useState } from 'react'
import { ChapterDto } from '@/lib/audio'
import { useNotification } from '@/contexts/notification-context'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { StatusIndicator } from '@/components/status/real-time-status'

interface ChapterListProps {
  chapters: ChapterDto[]
  onReorder: (chapterId: string, direction: 'up' | 'down') => Promise<void>
  onDelete: (chapterId: string) => Promise<void>
  onPlay?: (chapterId: string) => void
  onEdit?: (chapterId: string) => void
  onSelect?: (chapterId: string) => void
  selectedChapterId?: string
  currentlyPlayingId?: string
  className?: string
}

export function ChapterList({
  chapters,
  onReorder,
  onDelete,
  onPlay,
  onEdit,
  onSelect,
  selectedChapterId,
  currentlyPlayingId,
  className = ''
}: ChapterListProps) {
  const [chapterToDelete, setChapterToDelete] = useState<ChapterDto | null>(null)
  const [reordering, setReordering] = useState<string | null>(null)
  const { success, error: showError } = useNotification()

  const handleReorder = async (chapter: ChapterDto, direction: 'up' | 'down') => {
    setReordering(chapter.chapter_id)
    
    try {
      await onReorder(chapter.chapter_id, direction)
      success(`"${chapter.title}" 순서가 변경되었습니다.`)
    } catch (error) {
      showError('순서 변경에 실패했습니다.')
    } finally {
      setReordering(null)
    }
  }

  const handleDelete = async () => {
    if (!chapterToDelete) return

    try {
      await onDelete(chapterToDelete.chapter_id)
      setChapterToDelete(null)
      success(`"${chapterToDelete.title}" 챕터가 삭제되었습니다.`)
    } catch (error) {
      showError('챕터 삭제에 실패했습니다.')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800'
      case 'uploading':
        return 'bg-blue-100 text-blue-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'ready':
        return '준비됨'
      case 'processing':
        return '처리 중'
      case 'uploading':
        return '업로드 중'
      case 'error':
        return '오류'
      default:
        return '알 수 없음'
    }
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  if (chapters.length === 0) {
    return (
      <div className={`text-center py-12 bg-white rounded-lg border border-gray-200 ${className}`}>
        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">챕터가 없습니다</h3>
        <p className="text-gray-500 mb-4">아직 업로드된 오디오 파일이 없습니다.</p>
        <p className="text-sm text-gray-400">오디오 파일을 업로드하여 첫 번째 챕터를 만들어보세요.</p>
      </div>
    )
  }

  return (
    <div className={className}>
      <div className="space-y-3">
        {chapters.map((chapter, index) => (
          <div 
            key={chapter.chapter_id} 
            className={`border rounded-lg p-4 hover:shadow-sm transition-all cursor-pointer ${
              currentlyPlayingId === chapter.chapter_id
                ? 'border-green-500 bg-green-50'
                : selectedChapterId === chapter.chapter_id 
                ? 'border-blue-500 bg-blue-50' 
                : 'bg-white border-gray-200'
            }`}
            onClick={() => onSelect?.(chapter.chapter_id)}
          >
            <div className="flex items-start justify-between">
              {/* 왼쪽: 챕터 정보 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="flex items-center justify-center w-8 h-8 bg-gray-100 text-gray-600 text-sm font-medium rounded-full">
                    {chapter.chapter_number}
                  </span>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {chapter.title}
                    </h3>
                    <p className="text-xs text-gray-500 truncate">
                      {chapter.file_name}
                    </p>
                  </div>
                </div>
                
                {/* 메타데이터 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-600">
                  <div>
                    <span className="font-medium">재생시간</span>
                    <br />
                    <span>{formatDuration(chapter.duration)}</span>
                  </div>
                  <div>
                    <span className="font-medium">파일크기</span>
                    <br />
                    <span>{formatFileSize(chapter.file_size)}</span>
                  </div>
                  <div>
                    <span className="font-medium">상태</span>
                    <br />
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(chapter.status)}`}>
                      {getStatusText(chapter.status)}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">업로드일</span>
                    <br />
                    <span>{chapter.created_at ? new Date(chapter.created_at as any).toLocaleDateString('ko-KR') : '-'}</span>
                  </div>
                </div>
                
                {/* 설명 (있는 경우) */}
                {chapter.description && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-700">{chapter.description}</p>
                  </div>
                )}
              </div>
              
              {/* 오른쪽: 작업 버튼 */}
              <div className="flex flex-col space-y-2 ml-4">
                {/* 재생 버튼 */}
                {chapter.status === 'ready' && onPlay && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation() // 챕터 선택 이벤트 방지
                      onPlay(chapter.chapter_id)
                    }}
                    className={`p-2 rounded-full focus:outline-none focus:ring-2 ${
                      currentlyPlayingId === chapter.chapter_id
                        ? 'text-green-800 bg-green-100 hover:bg-green-200 focus:ring-green-500'
                        : 'text-green-600 hover:text-green-800 hover:bg-green-50 focus:ring-green-500'
                    }`}
                    aria-label={`${chapter.title} ${currentlyPlayingId === chapter.chapter_id ? '재생 중' : '재생'}`}
                    title={currentlyPlayingId === chapter.chapter_id ? '재생 중' : '재생'}
                  >
                    {currentlyPlayingId === chapter.chapter_id ? (
                      <div className="flex items-center">
                        <div className="animate-pulse h-5 w-5 flex items-center justify-center">
                          <div className="grid grid-cols-3 gap-0.5">
                            <div className="w-1 bg-green-600 animate-bounce" style={{ height: '8px', animationDelay: '0ms' }}></div>
                            <div className="w-1 bg-green-600 animate-bounce" style={{ height: '12px', animationDelay: '150ms' }}></div>
                            <div className="w-1 bg-green-600 animate-bounce" style={{ height: '8px', animationDelay: '300ms' }}></div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                )}
                
                {/* 편집 버튼 */}
                {onEdit && (
                  <button
                    onClick={() => onEdit(chapter.chapter_id)}
                    className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                    aria-label={`${chapter.title} 편집`}
                    title="편집"
                  >
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                )}
                
                {/* 순서 변경 버튼 */}
                <div className="flex flex-col space-y-1">
                  <button
                    onClick={() => handleReorder(chapter, 'up')}
                    disabled={index === 0 || reordering === chapter.chapter_id}
                    className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
                    aria-label={`${chapter.title} 위로 이동`}
                    title="위로 이동"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                  
                  <button
                    onClick={() => handleReorder(chapter, 'down')}
                    disabled={index === chapters.length - 1 || reordering === chapter.chapter_id}
                    className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
                    aria-label={`${chapter.title} 아래로 이동`}
                    title="아래로 이동"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
                
                {/* 삭제 버튼 */}
                <button
                  onClick={() => setChapterToDelete(chapter)}
                  className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-full focus:outline-none focus:ring-2 focus:ring-red-500"
                  aria-label={`${chapter.title} 삭제`}
                  title="삭제"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* 처리 중 상태 표시 */}
            {chapter.status === 'processing' && (
              <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600 mr-2"></div>
                  <span className="text-sm text-yellow-700">
                    오디오 파일을 처리하고 있습니다...
                  </span>
                </div>
              </div>
            )}
            
            {/* 에러 상태 표시 */}
            {chapter.status === 'error' && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded-md p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <svg className="h-4 w-4 text-red-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm text-red-700">
                      처리 중 오류가 발생했습니다.
                    </span>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        const response = await fetch(`/api/v1/files/retry-processing/${chapter.chapter_id}`, {
                          method: 'POST',
                          headers: {
                            'Authorization': `Bearer ${localStorage.getItem('voj_access_token')}`,
                          },
                        })

                        if (response.ok) {
                          success(`"${chapter.title}" 재처리가 시작되었습니다.`)
                          // 페이지 새로고침으로 상태 업데이트
                          setTimeout(() => window.location.reload(), 1000)
                        } else {
                          const errorData = await response.json().catch(() => ({ detail: 'Reprocessing failed' }))
                          throw new Error(errorData.detail)
                        }
                      } catch (error) {
                        showError(`재처리 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`)
                      }
                    }}
                    className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded"
                  >
                    재처리
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 삭제 확인 다이얼로그 */}
      <ConfirmDialog
        isOpen={chapterToDelete !== null}
        onClose={() => setChapterToDelete(null)}
        onConfirm={handleDelete}
        title="챕터 삭제 확인"
        message={`"${chapterToDelete?.title}" 챕터를 삭제하시겠습니까?<br/><br/>이 작업은 되돌릴 수 없으며, 오디오 파일도 함께 삭제됩니다.`}
        confirmText="삭제"
        cancelText="취소"
        destructive={true}
      />
    </div>
  )
}

interface ChapterStatsProps {
  chapters: ChapterDto[]
  className?: string
}

export function ChapterStats({ chapters, className = '' }: ChapterStatsProps) {
  const totalDuration = chapters.reduce((sum, chapter) => sum + chapter.duration, 0)
  const totalSize = chapters.reduce((sum, chapter) => sum + chapter.file_size, 0)
  
  const statusCounts = chapters.reduce((counts, chapter) => {
    counts[chapter.status] = (counts[chapter.status] || 0) + 1
    return counts
  }, {} as Record<string, number>)

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)

    if (hours > 0) {
      return `${hours}시간 ${minutes}분`
    } else {
      return `${minutes}분`
    }
  }

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(1)}MB`
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">챕터 통계</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{chapters.length}</div>
          <div className="text-sm text-gray-600">총 챕터</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{formatDuration(totalDuration)}</div>
          <div className="text-sm text-gray-600">총 재생시간</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{formatFileSize(totalSize)}</div>
          <div className="text-sm text-gray-600">총 파일크기</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{statusCounts['ready'] || 0}</div>
          <div className="text-sm text-gray-600">준비됨</div>
        </div>
      </div>
      
      {/* 상태별 세부 정보 */}
      {Object.keys(statusCounts).length > 1 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">상태별 현황</h4>
          <div className="space-y-1">
            {Object.entries(statusCounts).map(([status, count]) => (
              <div key={status} className="flex justify-between text-sm">
                <span className="text-gray-600">
                  {status === 'ready' ? '준비됨' :
                   status === 'processing' ? '처리 중' :
                   status === 'uploading' ? '업로드 중' :
                   status === 'error' ? '오류' : status}
                </span>
                <span className="font-medium">{count}개</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface ChapterSearchProps {
  chapters: ChapterDto[]
  onFilter: (filteredChapters: ChapterDto[]) => void
  className?: string
}

export function ChapterSearch({ chapters, onFilter, className = '' }: ChapterSearchProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const handleSearch = (term: string) => {
    setSearchTerm(term)
    applyFilters(term, statusFilter)
  }

  const handleStatusFilter = (status: string) => {
    setStatusFilter(status)
    applyFilters(searchTerm, status)
  }

  const applyFilters = (term: string, status: string) => {
    let filtered = chapters

    if (term) {
      const lowerTerm = term.toLowerCase()
      filtered = filtered.filter(chapter => 
        chapter.title.toLowerCase().includes(lowerTerm) ||
        chapter.file_name.toLowerCase().includes(lowerTerm) ||
        (chapter.description && chapter.description.toLowerCase().includes(lowerTerm))
      )
    }

    if (status) {
      filtered = filtered.filter(chapter => chapter.status === status)
    }

    onFilter(filtered)
  }

  const clearFilters = () => {
    setSearchTerm('')
    setStatusFilter('')
    onFilter(chapters)
  }

  const uniqueStatuses = [...new Set(chapters.map(c => c.status))]

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">챕터 검색 및 필터</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 검색 */}
        <div>
          <label htmlFor="chapter-search" className="block text-sm font-medium text-gray-700 mb-1">
            검색
          </label>
          <input
            id="chapter-search"
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="챕터 제목, 파일명 검색..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          />
        </div>

        {/* 상태 필터 */}
        <div>
          <label htmlFor="chapter-status-filter" className="block text-sm font-medium text-gray-700 mb-1">
            상태
          </label>
          <select
            id="chapter-status-filter"
            value={statusFilter}
            onChange={(e) => handleStatusFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          >
            <option value="">모든 상태</option>
            {uniqueStatuses.map(status => (
              <option key={status} value={status}>
                {status === 'ready' ? '준비됨' :
                 status === 'processing' ? '처리 중' :
                 status === 'uploading' ? '업로드 중' :
                 status === 'error' ? '오류' : status}
              </option>
            ))}
          </select>
        </div>

        {/* 필터 초기화 */}
        <div className="flex items-end">
          <button
            onClick={clearFilters}
            className="w-full px-3 py-2 text-sm text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            필터 초기화
          </button>
        </div>
      </div>
    </div>
  )
}
