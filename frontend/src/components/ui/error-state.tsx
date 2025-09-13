import React from 'react'
import Link from 'next/link'

interface ErrorStateProps {
  title?: string
  message: string
  action?: {
    label: string
    onClick: () => void
  }
  showRetry?: boolean
  onRetry?: () => void
  showHome?: boolean
  className?: string
}

export function ErrorState({
  title = '오류가 발생했습니다',
  message,
  action,
  showRetry = false,
  onRetry,
  showHome = false,
  className = ''
}: ErrorStateProps) {
  return (
    <div className={`bg-red-50 border border-red-200 rounded-md p-6 ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{message}</p>
          </div>
          
          {(action || showRetry || showHome) && (
            <div className="mt-4 flex space-x-3">
              {action && (
                <button
                  onClick={action.onClick}
                  className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  {action.label}
                </button>
              )}
              
              {showRetry && onRetry && (
                <button
                  onClick={onRetry}
                  className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  다시 시도
                </button>
              )}
              
              {showHome && (
                <Link
                  href="/books"
                  className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  목록으로 돌아가기
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface NetworkErrorProps {
  onRetry?: () => void
  showDetails?: boolean
  details?: string
}

export function NetworkError({ onRetry, showDetails = false, details }: NetworkErrorProps) {
  return (
    <ErrorState
      title="네트워크 오류"
      message="서버에 연결할 수 없습니다. 인터넷 연결을 확인하고 다시 시도해주세요."
      showRetry={!!onRetry}
      onRetry={onRetry}
      showHome={true}
    />
  )
}

interface NotFoundErrorProps {
  resourceName?: string
  homeLink?: string
}

export function NotFoundError({ 
  resourceName = '리소스', 
  homeLink = '/books' 
}: NotFoundErrorProps) {
  return (
    <ErrorState
      title={`${resourceName}를 찾을 수 없습니다`}
      message={`요청하신 ${resourceName}가 존재하지 않거나 접근 권한이 없습니다.`}
      showHome={true}
    />
  )
}

interface ValidationErrorProps {
  errors: Record<string, string>
  onDismiss?: () => void
}

export function ValidationError({ errors, onDismiss }: ValidationErrorProps) {
  const errorList = Object.entries(errors)
  
  return (
    <div className="bg-red-50 border border-red-200 rounded-md p-4" role="alert">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">입력 정보를 확인해주세요</h3>
          <div className="mt-2 text-sm text-red-700">
            <ul className="list-disc list-inside space-y-1">
              {errorList.map(([field, error]) => (
                <li key={field}>{error}</li>
              ))}
            </ul>
          </div>
          {onDismiss && (
            <div className="mt-4">
              <button
                onClick={onDismiss}
                className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
              >
                확인
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface SuccessNotificationProps {
  message: string
  onDismiss?: () => void
  autoHide?: boolean
  duration?: number
}

export function SuccessNotification({ 
  message, 
  onDismiss, 
  autoHide = true, 
  duration = 3000 
}: SuccessNotificationProps) {
  React.useEffect(() => {
    if (autoHide && onDismiss) {
      const timer = setTimeout(onDismiss, duration)
      return () => clearTimeout(timer)
    }
  }, [autoHide, duration, onDismiss])

  return (
    <div className="bg-green-50 border border-green-200 rounded-md p-4" role="alert">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-green-800">{message}</p>
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <button
              onClick={onDismiss}
              className="text-green-400 hover:text-green-600 focus:outline-none"
              aria-label="알림 닫기"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
