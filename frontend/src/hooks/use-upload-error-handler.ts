'use client'

import { useState, useCallback } from 'react'
import { useNotification } from '@/contexts/notification-context'

export type UploadErrorType = 
  | 'network'
  | 'validation' 
  | 'server'
  | 'timeout'
  | 'cancelled'
  | 'storage'
  | 'processing'
  | 'unknown'

export interface UploadError {
  type: UploadErrorType
  message: string
  details?: string
  retryable: boolean
  suggestedAction?: string
}

export interface RetryConfig {
  maxRetries: number
  baseDelay: number // ms
  maxDelay: number // ms
  backoffMultiplier: number
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2
}

export function useUploadErrorHandler() {
  const [retryAttempts, setRetryAttempts] = useState<Map<string, number>>(new Map())
  const { error: showError, warning, info } = useNotification()

  const parseUploadError = useCallback((error: Error | string, context?: any): UploadError => {
    const errorMessage = typeof error === 'string' ? error : error.message
    const lowerMessage = errorMessage.toLowerCase()

    // 네트워크 에러
    if (lowerMessage.includes('network') || lowerMessage.includes('fetch')) {
      return {
        type: 'network',
        message: '네트워크 연결에 문제가 있습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '인터넷 연결을 확인하고 다시 시도해주세요.'
      }
    }

    // 파일 크기 초과
    if (lowerMessage.includes('size') && lowerMessage.includes('limit')) {
      return {
        type: 'validation',
        message: '파일 크기가 제한을 초과했습니다.',
        details: errorMessage,
        retryable: false,
        suggestedAction: '파일 크기를 줄이거나 다른 파일을 선택해주세요.'
      }
    }

    // 파일 형식 오류
    if (lowerMessage.includes('format') || lowerMessage.includes('type')) {
      return {
        type: 'validation',
        message: '지원되지 않는 파일 형식입니다.',
        details: errorMessage,
        retryable: false,
        suggestedAction: 'WAV, MP3, M4A, FLAC 형식의 파일을 사용해주세요.'
      }
    }

    // 인증 오류
    if (lowerMessage.includes('unauthorized') || lowerMessage.includes('403') || lowerMessage.includes('401')) {
      return {
        type: 'server',
        message: '인증에 문제가 있습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '로그인을 다시 시도해주세요.'
      }
    }

    // 서버 오류
    if (lowerMessage.includes('500') || lowerMessage.includes('internal server')) {
      return {
        type: 'server',
        message: '서버에서 오류가 발생했습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '잠시 후 다시 시도해주세요.'
      }
    }

    // 타임아웃
    if (lowerMessage.includes('timeout') || lowerMessage.includes('시간초과')) {
      return {
        type: 'timeout',
        message: '업로드 시간이 초과되었습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '파일 크기가 클 경우 시간이 오래 걸릴 수 있습니다.'
      }
    }

    // 취소
    if (lowerMessage.includes('cancel') || lowerMessage.includes('abort')) {
      return {
        type: 'cancelled',
        message: '업로드가 취소되었습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '다시 업로드를 시작하세요.'
      }
    }

    // 스토리지 오류
    if (lowerMessage.includes('storage') || lowerMessage.includes('disk')) {
      return {
        type: 'storage',
        message: '파일 저장 중 오류가 발생했습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '서버 용량을 확인하고 다시 시도해주세요.'
      }
    }

    // 처리 오류
    if (lowerMessage.includes('processing') || lowerMessage.includes('ffmpeg') || lowerMessage.includes('metadata')) {
      return {
        type: 'processing',
        message: '오디오 파일 처리 중 오류가 발생했습니다.',
        details: errorMessage,
        retryable: true,
        suggestedAction: '파일이 손상되지 않았는지 확인해주세요.'
      }
    }

    // 기본 (알 수 없는 오류)
    return {
      type: 'unknown',
      message: '알 수 없는 오류가 발생했습니다.',
      details: errorMessage,
      retryable: true,
      suggestedAction: '문제가 지속되면 관리자에게 문의해주세요.'
    }
  }, [])

  const shouldRetry = useCallback((fileId: string, error: UploadError, config: RetryConfig = DEFAULT_RETRY_CONFIG): boolean => {
    if (!error.retryable) {
      return false
    }

    const attempts = retryAttempts.get(fileId) || 0
    return attempts < config.maxRetries
  }, [retryAttempts])

  const getRetryDelay = useCallback((fileId: string, config: RetryConfig = DEFAULT_RETRY_CONFIG): number => {
    const attempts = retryAttempts.get(fileId) || 0
    const delay = Math.min(
      config.baseDelay * Math.pow(config.backoffMultiplier, attempts),
      config.maxDelay
    )
    return delay
  }, [retryAttempts])

  const handleUploadError = useCallback((
    fileId: string, 
    fileName: string, 
    error: Error | string,
    onRetry?: () => void
  ) => {
    const uploadError = parseUploadError(error)
    const attempts = retryAttempts.get(fileId) || 0

    // 재시도 횟수 증가
    setRetryAttempts(prev => new Map(prev).set(fileId, attempts + 1))

    // 에러 타입별 알림
    const errorTitle = `"${fileName}" 업로드 실패`
    
    if (uploadError.retryable && shouldRetry(fileId, uploadError)) {
      const remainingRetries = DEFAULT_RETRY_CONFIG.maxRetries - attempts
      
      showError(
        `${uploadError.message} (${remainingRetries}회 재시도 가능)`,
        errorTitle
      )

      // 자동 재시도 제안
      if (onRetry && uploadError.type === 'network') {
        const delay = getRetryDelay(fileId)
        setTimeout(() => {
          info(`"${fileName}" 자동 재시도 중...`)
          onRetry()
        }, delay)
      }
    } else {
      // 재시도 불가능하거나 최대 횟수 초과
      showError(
        `${uploadError.message} ${uploadError.suggestedAction || ''}`,
        errorTitle
      )
    }

    return uploadError
  }, [parseUploadError, shouldRetry, getRetryDelay, retryAttempts, showError, info])

  const resetRetryCount = useCallback((fileId: string) => {
    setRetryAttempts(prev => {
      const newMap = new Map(prev)
      newMap.delete(fileId)
      return newMap
    })
  }, [])

  const getRetryInfo = useCallback((fileId: string) => {
    const attempts = retryAttempts.get(fileId) || 0
    const maxRetries = DEFAULT_RETRY_CONFIG.maxRetries
    
    return {
      attempts,
      maxRetries,
      remaining: Math.max(0, maxRetries - attempts),
      canRetry: attempts < maxRetries
    }
  }, [retryAttempts])

  const handleNetworkRecovery = useCallback(() => {
    // 네트워크 복구 시 실패한 업로드들 자동 재시도
    info('네트워크가 복구되었습니다. 실패한 업로드를 재시도합니다.')
  }, [info])

  return {
    handleUploadError,
    resetRetryCount,
    getRetryInfo,
    shouldRetry,
    getRetryDelay,
    handleNetworkRecovery,
    parseUploadError
  }
}

// 네트워크 상태 모니터링 훅
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [wasOffline, setWasOffline] = useState(false)

  React.useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      if (wasOffline) {
        setWasOffline(false)
        // 네트워크 복구 이벤트 발생
        window.dispatchEvent(new CustomEvent('network-recovered'))
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      setWasOffline(true)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [wasOffline])

  return { isOnline, wasOffline }
}
