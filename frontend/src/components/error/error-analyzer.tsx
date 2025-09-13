'use client'

import React, { useState } from 'react'

export interface ErrorInfo {
  type: 'upload' | 'encoding' | 'processing' | 'network' | 'validation' | 'system'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  technicalDetails?: string
  possibleCauses: string[]
  solutions: string[]
  preventionTips?: string[]
  relatedLinks?: Array<{ title: string; url: string }>
}

interface ErrorAnalyzerProps {
  error: string | Error
  context?: {
    chapterId?: string
    fileName?: string
    fileSize?: number
    operation?: string
  }
  className?: string
}

export function ErrorAnalyzer({ error, context, className = '' }: ErrorAnalyzerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const errorInfo = analyzeError(error, context)

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'border-blue-200 bg-blue-50 text-blue-800'
      case 'medium':
        return 'border-yellow-200 bg-yellow-50 text-yellow-800'
      case 'high':
        return 'border-orange-200 bg-orange-50 text-orange-800'
      case 'critical':
        return 'border-red-200 bg-red-50 text-red-800'
      default:
        return 'border-gray-200 bg-gray-50 text-gray-800'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low':
        return (
          <svg className="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'medium':
        return (
          <svg className="h-5 w-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        )
      case 'high':
        return (
          <svg className="h-5 w-5 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'critical':
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  return (
    <div className={`border rounded-lg ${getSeverityColor(errorInfo.severity)} ${className}`}>
      <div className="p-4">
        {/* 헤더 */}
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            {getSeverityIcon(errorInfo.severity)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">
                {errorInfo.message}
              </h4>
              <span className="text-xs px-2 py-1 rounded uppercase font-medium">
                {errorInfo.severity} • {errorInfo.type}
              </span>
            </div>
            
            {context && (
              <div className="mt-1 text-xs opacity-75">
                {context.fileName && `파일: ${context.fileName}`}
                {context.operation && ` | 작업: ${context.operation}`}
              </div>
            )}
          </div>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-shrink-0 text-sm text-gray-600 hover:text-gray-800"
          >
            {isExpanded ? '접기' : '자세히'}
          </button>
        </div>

        {/* 확장된 내용 */}
        {isExpanded && (
          <div className="mt-4 space-y-4">
            {/* 가능한 원인 */}
            <div>
              <h5 className="text-sm font-medium mb-2">가능한 원인</h5>
              <ul className="text-sm space-y-1">
                {errorInfo.possibleCauses.map((cause, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-gray-400 mt-1">•</span>
                    <span>{cause}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 해결 방법 */}
            <div>
              <h5 className="text-sm font-medium mb-2">해결 방법</h5>
              <ol className="text-sm space-y-2">
                {errorInfo.solutions.map((solution, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="flex-shrink-0 w-5 h-5 bg-blue-100 text-blue-600 text-xs font-medium rounded-full flex items-center justify-center mt-0.5">
                      {index + 1}
                    </span>
                    <span>{solution}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* 예방 팁 */}
            {errorInfo.preventionTips && errorInfo.preventionTips.length > 0 && (
              <div>
                <h5 className="text-sm font-medium mb-2">예방 팁</h5>
                <ul className="text-sm space-y-1">
                  {errorInfo.preventionTips.map((tip, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <svg className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 관련 링크 */}
            {errorInfo.relatedLinks && errorInfo.relatedLinks.length > 0 && (
              <div>
                <h5 className="text-sm font-medium mb-2">관련 도움말</h5>
                <div className="space-y-1">
                  {errorInfo.relatedLinks.map((link, index) => (
                    <a
                      key={index}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800 underline block"
                    >
                      {link.title}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* 기술적 세부사항 */}
            {errorInfo.technicalDetails && (
              <details className="mt-4">
                <summary className="text-sm font-medium text-gray-700 cursor-pointer">
                  기술적 세부사항
                </summary>
                <pre className="mt-2 text-xs text-gray-600 bg-gray-100 p-3 rounded overflow-x-auto">
                  {errorInfo.technicalDetails}
                </pre>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function analyzeError(error: string | Error, context?: any): ErrorInfo {
  const errorMessage = typeof error === 'string' ? error : error.message
  const lowerMessage = errorMessage.toLowerCase()

  // 파일 크기 오류
  if (lowerMessage.includes('size') && lowerMessage.includes('limit')) {
    return {
      type: 'validation',
      severity: 'medium',
      message: '파일 크기가 제한을 초과했습니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '업로드하려는 파일이 100MB를 초과함',
        '파일이 손상되어 크기 정보가 잘못됨'
      ],
      solutions: [
        '파일 크기를 확인하고 100MB 이하의 파일을 사용하세요',
        '긴 오디오는 여러 부분으로 나누어 업로드하세요',
        '오디오 편집 프로그램으로 파일을 압축하세요'
      ],
      preventionTips: [
        '업로드 전에 파일 크기를 미리 확인하세요',
        '고품질 오디오는 필요에 따라 비트레이트를 조정하세요'
      ]
    }
  }

  // 파일 형식 오류
  if (lowerMessage.includes('format') || lowerMessage.includes('type')) {
    return {
      type: 'validation',
      severity: 'medium',
      message: '지원되지 않는 파일 형식입니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '파일 확장자가 지원되지 않음',
        '파일 내용과 확장자가 일치하지 않음',
        '손상된 파일 헤더'
      ],
      solutions: [
        'MP3, WAV, M4A, FLAC 형식의 파일을 사용하세요',
        '파일을 다른 형식으로 변환해보세요',
        '파일이 손상되지 않았는지 확인하세요'
      ],
      preventionTips: [
        '신뢰할 수 있는 오디오 편집 프로그램을 사용하세요',
        '파일 변환 시 원본을 백업하세요'
      ],
      relatedLinks: [
        { title: '지원되는 오디오 형식', url: '/docs/supported-formats' }
      ]
    }
  }

  // 네트워크 오류
  if (lowerMessage.includes('network') || lowerMessage.includes('connection') || lowerMessage.includes('timeout')) {
    return {
      type: 'network',
      severity: 'high',
      message: '네트워크 연결에 문제가 있습니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '인터넷 연결이 불안정함',
        '서버가 일시적으로 응답하지 않음',
        '방화벽이나 프록시가 연결을 차단함',
        '업로드 시간이 너무 오래 걸림'
      ],
      solutions: [
        '인터넷 연결 상태를 확인하세요',
        '잠시 후 다시 시도하세요',
        'Wi-Fi 대신 유선 연결을 사용해보세요',
        'VPN을 사용 중이라면 일시적으로 해제해보세요',
        '브라우저를 새로고침하고 다시 시도하세요'
      ],
      preventionTips: [
        '안정적인 네트워크 환경에서 업로드하세요',
        '큰 파일은 네트워크가 안정적인 시간에 업로드하세요'
      ]
    }
  }

  // 인코딩 오류
  if (lowerMessage.includes('encoding') || lowerMessage.includes('ffmpeg')) {
    return {
      type: 'encoding',
      severity: 'high',
      message: '오디오 인코딩 중 오류가 발생했습니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '오디오 파일이 손상됨',
        '지원되지 않는 오디오 코덱',
        '서버 리소스 부족',
        '인코딩 프로세스 타임아웃'
      ],
      solutions: [
        '파일을 다른 형식으로 변환 후 다시 업로드하세요',
        '파일이 정상적으로 재생되는지 확인하세요',
        '잠시 후 다시 시도하세요 (서버 부하 감소 대기)',
        '파일을 더 작은 크기로 분할해보세요'
      ],
      preventionTips: [
        '업로드 전에 오디오 파일을 테스트 재생해보세요',
        '표준적인 오디오 형식(MP3, WAV)을 사용하세요'
      ]
    }
  }

  // 인증 오류
  if (lowerMessage.includes('unauthorized') || lowerMessage.includes('authentication')) {
    return {
      type: 'system',
      severity: 'critical',
      message: '인증에 문제가 있습니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '로그인 세션이 만료됨',
        '권한이 부족함',
        '계정이 비활성화됨'
      ],
      solutions: [
        '로그아웃 후 다시 로그인하세요',
        '페이지를 새로고침하고 다시 시도하세요',
        '관리자에게 권한을 요청하세요'
      ]
    }
  }

  // 서버 오류
  if (lowerMessage.includes('500') || lowerMessage.includes('server') || lowerMessage.includes('internal')) {
    return {
      type: 'system',
      severity: 'critical',
      message: '서버에서 오류가 발생했습니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '서버 내부 오류',
        '데이터베이스 연결 문제',
        '스토리지 용량 부족',
        '서버 과부하'
      ],
      solutions: [
        '잠시 후 다시 시도하세요',
        '브라우저 캐시를 지우고 다시 시도하세요',
        '문제가 지속되면 관리자에게 문의하세요'
      ],
      preventionTips: [
        '업로드 중에는 브라우저 탭을 닫지 마세요',
        '동시에 많은 파일을 업로드하지 마세요'
      ]
    }
  }

  // 파일 처리 오류
  if (lowerMessage.includes('processing') || lowerMessage.includes('metadata')) {
    return {
      type: 'processing',
      severity: 'medium',
      message: '파일 처리 중 오류가 발생했습니다',
      technicalDetails: errorMessage,
      possibleCauses: [
        '오디오 파일의 메타데이터가 손상됨',
        '지원되지 않는 오디오 인코딩',
        '파일 구조가 비표준적임'
      ],
      solutions: [
        '오디오 편집 프로그램으로 파일을 다시 저장하세요',
        '다른 형식으로 변환 후 업로드하세요',
        '파일이 정상적으로 재생되는지 확인하세요'
      ],
      preventionTips: [
        '표준적인 오디오 편집 프로그램을 사용하세요',
        '파일 변환 시 메타데이터를 보존하세요'
      ]
    }
  }

  // 기본 오류 (분류되지 않은 경우)
  return {
    type: 'system',
    severity: 'medium',
    message: '알 수 없는 오류가 발생했습니다',
    technicalDetails: errorMessage,
    possibleCauses: [
      '예상치 못한 시스템 오류',
      '브라우저 호환성 문제',
      '일시적인 서비스 장애'
    ],
    solutions: [
      '페이지를 새로고침하고 다시 시도하세요',
      '다른 브라우저에서 시도해보세요',
      '잠시 후 다시 시도하세요',
      '문제가 지속되면 관리자에게 문의하세요'
    ],
    preventionTips: [
      '최신 브라우저를 사용하세요',
      '브라우저 확장 프로그램을 일시 비활성화해보세요'
    ]
  }
}

interface QuickErrorSolutionProps {
  error: string | Error
  onRetry?: () => void
  onDismiss?: () => void
  className?: string
}

export function QuickErrorSolution({ 
  error, 
  onRetry, 
  onDismiss, 
  className = '' 
}: QuickErrorSolutionProps) {
  const errorInfo = analyzeError(error)
  const primarySolution = errorInfo.solutions[0]

  return (
    <div className={`border border-red-200 bg-red-50 rounded-lg p-3 ${className}`}>
      <div className="flex items-start space-x-3">
        <svg className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-red-800">
            {errorInfo.message}
          </h4>
          <p className="mt-1 text-sm text-red-700">
            {primarySolution}
          </p>
        </div>
        
        <div className="flex-shrink-0 flex space-x-2">
          {onRetry && errorInfo.type !== 'validation' && (
            <button
              onClick={onRetry}
              className="text-sm bg-red-100 text-red-700 px-2 py-1 rounded hover:bg-red-200"
            >
              다시 시도
            </button>
          )}
          
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-red-400 hover:text-red-600"
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

interface ErrorSummaryProps {
  errors: Array<{ id: string; error: string | Error; context?: any }>
  onResolveAll?: () => void
  className?: string
}

export function ErrorSummary({ errors, onResolveAll, className = '' }: ErrorSummaryProps) {
  const errorsByType = errors.reduce((acc, { error, context }) => {
    const info = analyzeError(error, context)
    if (!acc[info.type]) {
      acc[info.type] = []
    }
    acc[info.type].push(info)
    return acc
  }, {} as Record<string, ErrorInfo[]>)

  const criticalCount = errors.filter(({ error, context }) => 
    analyzeError(error, context).severity === 'critical'
  ).length

  if (errors.length === 0) {
    return null
  }

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-medium text-red-800">
          오류 요약 ({errors.length}개)
          {criticalCount > 0 && (
            <span className="ml-2 text-sm bg-red-200 text-red-800 px-2 py-1 rounded">
              긴급 {criticalCount}개
            </span>
          )}
        </h3>
        
        {onResolveAll && (
          <button
            onClick={onResolveAll}
            className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200"
          >
            모두 해결 시도
          </button>
        )}
      </div>
      
      <div className="space-y-2">
        {Object.entries(errorsByType).map(([type, typeErrors]) => (
          <div key={type} className="text-sm">
            <span className="font-medium text-red-700 capitalize">
              {type === 'upload' ? '업로드' :
               type === 'encoding' ? '인코딩' :
               type === 'processing' ? '처리' :
               type === 'network' ? '네트워크' :
               type === 'validation' ? '검증' :
               type === 'system' ? '시스템' : type}
            </span>
            <span className="ml-2 text-red-600">
              {typeErrors.length}개 오류
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
