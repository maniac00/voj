'use client'

import React, { useState, useEffect } from 'react'
import { UploadError, useUploadErrorHandler, useNetworkStatus } from '@/hooks/use-upload-error-handler'

interface UploadErrorDisplayProps {
  error: UploadError
  fileName: string
  fileId: string
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
}

export function UploadErrorDisplay({
  error,
  fileName,
  fileId,
  onRetry,
  onDismiss,
  className = ''
}: UploadErrorDisplayProps) {
  const { getRetryInfo } = useUploadErrorHandler()
  const retryInfo = getRetryInfo(fileId)

  const getErrorIcon = () => {
    switch (error.type) {
      case 'network':
        return (
          <svg className="h-5 w-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        )
      case 'validation':
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'server':
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'timeout':
        return (
          <svg className="h-5 w-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const getErrorColor = () => {
    switch (error.type) {
      case 'network':
        return 'border-orange-200 bg-orange-50'
      case 'validation':
        return 'border-red-200 bg-red-50'
      case 'timeout':
        return 'border-yellow-200 bg-yellow-50'
      default:
        return 'border-red-200 bg-red-50'
    }
  }

  const getTextColor = () => {
    switch (error.type) {
      case 'network':
        return 'text-orange-700'
      case 'validation':
        return 'text-red-700'
      case 'timeout':
        return 'text-yellow-700'
      default:
        return 'text-red-700'
    }
  }

  return (
    <div className={`border rounded-md p-4 ${getErrorColor()} ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getErrorIcon()}
        </div>
        
        <div className="ml-3 flex-1">
          <h4 className={`text-sm font-medium ${getTextColor()}`}>
            {fileName} - {error.message}
          </h4>
          
          {error.suggestedAction && (
            <p className={`mt-1 text-sm ${getTextColor()}`}>
              {error.suggestedAction}
            </p>
          )}
          
          {error.retryable && (
            <div className="mt-2 text-xs text-gray-600">
              재시도 {retryInfo.attempts}/{retryInfo.maxRetries} 
              {retryInfo.remaining > 0 && ` (${retryInfo.remaining}회 남음)`}
            </div>
          )}
          
          {/* 상세 정보 (개발 모드에서만) */}
          {process.env.NODE_ENV === 'development' && error.details && (
            <details className="mt-2">
              <summary className="text-xs text-gray-500 cursor-pointer">상세 정보</summary>
              <pre className="mt-1 text-xs text-gray-600 whitespace-pre-wrap">
                {error.details}
              </pre>
            </details>
          )}
        </div>
        
        <div className="ml-4 flex-shrink-0 space-x-2">
          {error.retryable && onRetry && retryInfo.canRetry && (
            <button
              onClick={onRetry}
              className="text-sm px-3 py-1 bg-white border border-gray-300 rounded text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              재시도
            </button>
          )}
          
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
              aria-label="에러 메시지 닫기"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

interface NetworkStatusIndicatorProps {
  className?: string
}

export function NetworkStatusIndicator({ className = '' }: NetworkStatusIndicatorProps) {
  const { isOnline, wasOffline } = useNetworkStatus()
  const [showStatus, setShowStatus] = useState(false)

  useEffect(() => {
    if (!isOnline || wasOffline) {
      setShowStatus(true)
      
      // 온라인 상태에서 5초 후 숨김
      if (isOnline && wasOffline) {
        const timer = setTimeout(() => setShowStatus(false), 5000)
        return () => clearTimeout(timer)
      }
    }
  }, [isOnline, wasOffline])

  if (!showStatus) return null

  return (
    <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 ${className}`}>
      <div className={`rounded-md px-4 py-2 shadow-lg ${
        isOnline 
          ? 'bg-green-100 border border-green-200 text-green-800'
          : 'bg-red-100 border border-red-200 text-red-800'
      }`}>
        <div className="flex items-center space-x-2">
          {isOnline ? (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-12.728 12.728m0 0L12 12m-6.364 6.364L12 12m6.364-6.364L12 12" />
            </svg>
          )}
          <span className="text-sm font-medium">
            {isOnline ? '네트워크 연결됨' : '네트워크 연결 끊김'}
          </span>
        </div>
      </div>
    </div>
  )
}

interface BulkErrorHandlerProps {
  errors: Array<{
    fileId: string
    fileName: string
    error: UploadError
  }>
  onRetryAll?: () => void
  onDismissAll?: () => void
  className?: string
}

export function BulkErrorHandler({
  errors,
  onRetryAll,
  onDismissAll,
  className = ''
}: BulkErrorHandlerProps) {
  const retryableErrors = errors.filter(e => e.error.retryable)
  const nonRetryableErrors = errors.filter(e => !e.error.retryable)

  if (errors.length === 0) return null

  return (
    <div className={`bg-red-50 border border-red-200 rounded-md p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            업로드 오류 ({errors.length}개 파일)
          </h3>
          
          <div className="mt-2 text-sm text-red-700">
            <div className="space-y-1">
              {retryableErrors.length > 0 && (
                <p>• {retryableErrors.length}개 파일 재시도 가능</p>
              )}
              {nonRetryableErrors.length > 0 && (
                <p>• {nonRetryableErrors.length}개 파일 수정 필요</p>
              )}
            </div>
            
            <div className="mt-3 space-y-1">
              {errors.slice(0, 3).map(({ fileName, error }) => (
                <div key={fileName} className="text-xs">
                  <strong>{fileName}:</strong> {error.message}
                </div>
              ))}
              {errors.length > 3 && (
                <div className="text-xs text-red-600">
                  ...외 {errors.length - 3}개 파일
                </div>
              )}
            </div>
          </div>
          
          <div className="mt-4 flex space-x-3">
            {retryableErrors.length > 0 && onRetryAll && (
              <button
                onClick={onRetryAll}
                className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                재시도 가능한 파일 다시 업로드
              </button>
            )}
            
            {onDismissAll && (
              <button
                onClick={onDismissAll}
                className="text-sm text-red-600 hover:text-red-800"
              >
                모든 오류 닫기
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

interface UploadTroubleshootingProps {
  className?: string
}

export function UploadTroubleshooting({ className = '' }: UploadTroubleshootingProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-md p-4 ${className}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <h3 className="text-sm font-medium text-blue-800">
          업로드 문제 해결 가이드
        </h3>
        <svg 
          className={`h-4 w-4 text-blue-600 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isExpanded && (
        <div className="mt-3 text-sm text-blue-700 space-y-3">
          <div>
            <h4 className="font-medium">파일 형식 오류</h4>
            <p>• 지원 형식: MP3, WAV, M4A, FLAC</p>
            <p>• 파일 확장자와 실제 형식이 일치하는지 확인</p>
          </div>
          
          <div>
            <h4 className="font-medium">파일 크기 문제</h4>
            <p>• 최대 크기: 100MB</p>
            <p>• 긴 오디오는 여러 파트로 분할 권장</p>
          </div>
          
          <div>
            <h4 className="font-medium">네트워크 문제</h4>
            <p>• 안정한 Wi-Fi 연결 사용</p>
            <p>• 브라우저 새로고침 후 재시도</p>
            <p>• VPN 사용 시 일시 해제</p>
          </div>
          
          <div>
            <h4 className="font-medium">파일명 문제</h4>
            <p>• 특수문자 사용 금지 (영문, 한글, 숫자, -, _ 만 허용)</p>
            <p>• 파일명 길이 255자 이하</p>
          </div>
          
          <div>
            <h4 className="font-medium">서버 오류</h4>
            <p>• 잠시 후 다시 시도</p>
            <p>• 문제 지속 시 관리자 문의</p>
          </div>
        </div>
      )}
    </div>
  )
}

interface AutoRetryManagerProps {
  failedUploads: Array<{
    fileId: string
    fileName: string
    retryFunction: () => Promise<void>
  }>
  onRetryComplete?: (fileId: string, success: boolean) => void
}

export function AutoRetryManager({ failedUploads, onRetryComplete }: AutoRetryManagerProps) {
  const [retryingFiles, setRetryingFiles] = useState<Set<string>>(new Set())
  const { handleNetworkRecovery } = useUploadErrorHandler()

  useEffect(() => {
    const handleNetworkRecovered = async () => {
      handleNetworkRecovery()
      
      // 네트워크 복구 시 실패한 업로드들 자동 재시도
      for (const upload of failedUploads) {
        if (!retryingFiles.has(upload.fileId)) {
          setRetryingFiles(prev => new Set(prev).add(upload.fileId))
          
          try {
            await new Promise(resolve => setTimeout(resolve, 1000)) // 1초 지연
            await upload.retryFunction()
            onRetryComplete?.(upload.fileId, true)
          } catch (error) {
            onRetryComplete?.(upload.fileId, false)
          } finally {
            setRetryingFiles(prev => {
              const newSet = new Set(prev)
              newSet.delete(upload.fileId)
              return newSet
            })
          }
        }
      }
    }

    window.addEventListener('network-recovered', handleNetworkRecovered)
    return () => window.removeEventListener('network-recovered', handleNetworkRecovered)
  }, [failedUploads, retryingFiles, handleNetworkRecovery, onRetryComplete])

  return null // 이 컴포넌트는 UI를 렌더링하지 않음
}
