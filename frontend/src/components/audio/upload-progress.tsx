'use client'

import React from 'react'
import { UploadProgress } from '@/hooks/use-file-upload'

interface UploadProgressBarProps {
  progress: UploadProgress
  status: 'pending' | 'uploading' | 'completed' | 'error'
  fileName: string
  error?: string
  onCancel?: () => void
  onRetry?: () => void
  onRemove?: () => void
  className?: string
}

export function UploadProgressBar({
  progress,
  status,
  fileName,
  error,
  onCancel,
  onRetry,
  onRemove,
  className = ''
}: UploadProgressBarProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800'
      case 'uploading':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'error':
        return 'bg-red-100 text-red-800'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return '대기 중'
      case 'uploading':
        return '업로드 중'
      case 'completed':
        return '완료'
      case 'error':
        return '오류'
    }
  }

  const getProgressBarColor = () => {
    switch (status) {
      case 'uploading':
        return 'bg-blue-500'
      case 'completed':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-300'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatSpeed = (bytesPerSecond: number) => {
    return formatFileSize(bytesPerSecond) + '/s'
  }

  return (
    <div className={`border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 truncate" title={fileName}>
            {fileName}
          </h4>
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-xs text-gray-500">
              {formatFileSize(progress.total)}
            </span>
            {status === 'uploading' && progress.loaded > 0 && (
              <>
                <span className="text-xs text-gray-400">•</span>
                <span className="text-xs text-gray-500">
                  {formatFileSize(progress.loaded)} / {formatFileSize(progress.total)}
                </span>
              </>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <span 
            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor()}`}
            aria-label={`상태: ${getStatusText()}`}
          >
            {getStatusText()}
          </span>
          
          {status === 'uploading' && onCancel && (
            <button
              onClick={onCancel}
              className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
              aria-label="업로드 취소"
            >
              취소
            </button>
          )}
          
          {status === 'error' && onRetry && (
            <button
              onClick={onRetry}
              className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded"
              aria-label="재시도"
            >
              재시도
            </button>
          )}
          
          {(status === 'completed' || status === 'error') && onRemove && (
            <button
              onClick={onRemove}
              className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
              aria-label="목록에서 제거"
            >
              제거
            </button>
          )}
        </div>
      </div>
      
      {/* 진행률 바 */}
      <div className="mb-2">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>진행률</span>
          <span>{progress.percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor()}`}
            style={{ width: `${progress.percentage}%` }}
            role="progressbar"
            aria-valuenow={progress.percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${fileName} 업로드 진행률`}
          />
        </div>
      </div>
      
      {/* 에러 메시지 */}
      {status === 'error' && error && (
        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded" role="alert">
          <strong>오류:</strong> {error}
        </div>
      )}
      
      {/* 업로드 속도 (업로드 중일 때만) */}
      {status === 'uploading' && progress.loaded > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          {/* 간단한 속도 계산은 복잡하므로 생략 */}
          <span>업로드 중...</span>
        </div>
      )}
    </div>
  )
}

interface BatchUploadProgressProps {
  items: Array<{
    id: string
    file: File
    progress: UploadProgress
    status: 'pending' | 'uploading' | 'completed' | 'error'
    error?: string
  }>
  onCancel: (id: string) => void
  onRetry: (id: string) => void
  onRemove: (id: string) => void
  onClearCompleted: () => void
  className?: string
}

export function BatchUploadProgress({
  items,
  onCancel,
  onRetry,
  onRemove,
  onClearCompleted,
  className = ''
}: BatchUploadProgressProps) {
  const completedCount = items.filter(item => item.status === 'completed').length
  const errorCount = items.filter(item => item.status === 'error').length
  const uploadingCount = items.filter(item => item.status === 'uploading').length
  const pendingCount = items.filter(item => item.status === 'pending').length

  const totalProgress = items.length > 0 
    ? Math.round((completedCount / items.length) * 100)
    : 0

  if (items.length === 0) return null

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">업로드 진행 상황</h3>
          <div className="text-sm text-gray-600">
            {completedCount}/{items.length} 완료
          </div>
        </div>
        
        {/* 전체 진행률 */}
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-600 mb-1">
            <span>전체 진행률</span>
            <span>{totalProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="h-2 rounded-full bg-blue-500 transition-all duration-300"
              style={{ width: `${totalProgress}%` }}
            />
          </div>
        </div>

        {/* 상태 요약 */}
        <div className="mt-3 flex items-center space-x-4 text-xs text-gray-600">
          {pendingCount > 0 && <span>대기: {pendingCount}개</span>}
          {uploadingCount > 0 && <span>업로드 중: {uploadingCount}개</span>}
          {completedCount > 0 && <span className="text-green-600">완료: {completedCount}개</span>}
          {errorCount > 0 && <span className="text-red-600">오류: {errorCount}개</span>}
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-3" role="log" aria-live="polite" aria-label="업로드 진행 상황">
          {items.map((item) => (
            <UploadProgressBar
              key={item.id}
              progress={item.progress}
              status={item.status}
              fileName={item.file.name}
              error={item.error}
              onCancel={item.status === 'uploading' ? () => onCancel(item.id) : undefined}
              onRetry={item.status === 'error' ? () => onRetry(item.id) : undefined}
              onRemove={(item.status === 'completed' || item.status === 'error') ? () => onRemove(item.id) : undefined}
            />
          ))}
        </div>
        
        {/* 일괄 작업 버튼 */}
        {items.length > 0 && (
          <div className="mt-4 flex justify-between items-center pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              총 {items.length}개 파일
            </div>
            
            <div className="space-x-2">
              {errorCount > 0 && (
                <button
                  onClick={() => {
                    items.filter(i => i.status === 'error').forEach(item => onRetry(item.id))
                  }}
                  className="text-sm px-3 py-1 text-blue-600 hover:text-blue-800"
                >
                  오류 항목 재시도
                </button>
              )}
              
              {(completedCount > 0 || errorCount > 0) && (
                <button
                  onClick={onClearCompleted}
                  className="text-sm px-3 py-1 text-gray-600 hover:text-gray-800"
                >
                  완료된 항목 정리
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
