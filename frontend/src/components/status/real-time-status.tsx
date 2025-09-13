'use client'

import React from 'react'
import { useChapterStatus, ChapterStatus } from '@/hooks/use-websocket-logs'
import { AudioMetadataDisplay, MetadataProgress } from '@/components/metadata/audio-metadata-display'

interface RealTimeStatusProps {
  chapterId: string
  className?: string
}

export function RealTimeStatus({ chapterId, className = '' }: RealTimeStatusProps) {
  const { status, connectionStatus, error, requestStatus } = useChapterStatus({
    chapterId,
    autoConnect: true
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'processing':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'uploading':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
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
        return status || '알 수 없음'
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

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <svg className="h-5 w-5 text-red-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-red-700">상태 조회 실패: {error}</span>
        </div>
      </div>
    )
  }

  if (!status) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
          <span className="text-sm text-gray-600">상태 정보를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
      {/* 헤더 */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">실시간 상태</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' : 
              connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
              'bg-red-500'
            }`} />
            <button
              onClick={requestStatus}
              className="text-sm text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
            >
              새로고침
            </button>
          </div>
        </div>
      </div>

      {/* 챕터 정보 */}
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">{status.chapter_title}</h4>
            {status.file_name && (
              <p className="text-xs text-gray-500">{status.file_name}</p>
            )}
          </div>
          <span className={`inline-flex px-3 py-1 text-sm font-medium rounded-full border ${getStatusColor(status.chapter_status)}`}>
            {getStatusText(status.chapter_status)}
          </span>
        </div>

        {/* 인코딩 작업 정보 */}
        {status.encoding_job && (
          <div className="bg-gray-50 rounded-lg p-3">
            <h5 className="text-sm font-medium text-gray-700 mb-2">인코딩 작업</h5>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">상태</span>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded ${getStatusColor(status.encoding_job.status)}`}>
                  {getStatusText(status.encoding_job.status)}
                </span>
              </div>
              
              {status.encoding_job.progress > 0 && (
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>진행률</span>
                    <span>{Math.round(status.encoding_job.progress * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${status.encoding_job.progress * 100}%` }}
                    />
                  </div>
                </div>
              )}
              
              {status.encoding_job.retry_count > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">재시도</span>
                  <span className="text-xs text-yellow-600">
                    {status.encoding_job.retry_count}회
                  </span>
                </div>
              )}
              
              {status.encoding_job.error_message && (
                <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                  {status.encoding_job.error_message}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 메타데이터 표시 */}
        {status.metadata ? (
          <AudioMetadataDisplay
            metadata={{
              duration: status.metadata.duration,
              bitrate: status.metadata.bitrate,
              sample_rate: status.metadata.sample_rate,
              channels: status.metadata.channels,
              format: status.metadata.format
            }}
            showTechnicalDetails={true}
          />
        ) : status.encoding_job?.status === 'processing' ? (
          <MetadataProgress
            progress={status.encoding_job.progress}
            currentStep={
              status.encoding_job.progress < 0.3 ? '파일 검증 중...' :
              status.encoding_job.progress < 0.5 ? '인코딩 준비 중...' :
              status.encoding_job.progress < 0.8 ? '오디오 변환 중...' :
              '메타데이터 추출 중...'
            }
          />
        ) : (
          <div className="bg-gray-50 rounded-lg p-3 text-center text-sm text-gray-600">
            메타데이터를 추출하는 중입니다...
          </div>
        )}

        {/* 타임스탬프 */}
        <div className="text-xs text-gray-500 text-center">
          마지막 업데이트: {new Date(status.timestamp).toLocaleString('ko-KR')}
        </div>
      </div>
    </div>
  )
}

interface StatusIndicatorProps {
  status: string
  progress?: number
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  className?: string
}

export function StatusIndicator({ 
  status, 
  progress, 
  size = 'md', 
  showText = true,
  className = '' 
}: StatusIndicatorProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'ready':
        return (
          <svg className={`${sizeClasses[size]} text-green-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        )
      case 'processing':
        return (
          <div className={`${sizeClasses[size]} relative`}>
            <div className="animate-spin rounded-full border-2 border-yellow-200 border-t-yellow-500"></div>
            {progress !== undefined && (
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-yellow-600">
                  {Math.round(progress * 100)}
                </span>
              </div>
            )}
          </div>
        )
      case 'uploading':
        return (
          <div className={`animate-spin rounded-full border-2 border-blue-200 border-t-blue-500 ${sizeClasses[size]}`}></div>
        )
      case 'error':
        return (
          <svg className={`${sizeClasses[size]} text-red-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        )
      default:
        return (
          <div className={`rounded-full bg-gray-300 ${sizeClasses[size]}`}></div>
        )
    }
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {getStatusIcon()}
      {showText && (
        <span className="text-sm text-gray-700">
          {status === 'ready' ? '준비됨' :
           status === 'processing' ? '처리 중' :
           status === 'uploading' ? '업로드 중' :
           status === 'error' ? '오류' : status}
          {progress !== undefined && status === 'processing' && (
            <span className="ml-1 text-gray-500">
              ({Math.round(progress * 100)}%)
            </span>
          )}
        </span>
      )}
    </div>
  )
}
