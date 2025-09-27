'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useWebSocketLogs, LogMessage } from '@/hooks/use-websocket-logs'
import { ErrorAnalyzer, QuickErrorSolution } from '@/components/error/error-analyzer'
import { LogFilter, LogSearch } from '@/components/logs/log-filter'

interface RealTimeLogsProps {
  chapterId?: string
  maxHeight?: string
  autoScroll?: boolean
  showFilters?: boolean
  onLogsUpdate?: (logs: LogMessage[]) => void
  className?: string
}

export function RealTimeLogs({
  chapterId,
  maxHeight = '400px',
  autoScroll: autoScrollProp = true,
  showFilters = true,
  onLogsUpdate,
  className = ''
}: RealTimeLogsProps) {
  const { logs, connectionStatus, error, connect, disconnect, clearLogs } = useWebSocketLogs({
    chapterId,
    autoConnect: true,
    maxLogHistory: 200
  })

  const [filteredLogs, setFilteredLogs] = useState<LogMessage[]>([])
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [autoScrollState, setAutoScrollState] = useState<boolean>(autoScrollProp)
  const logsEndRef = useRef<HTMLDivElement>(null)

  // 초기 로그 설정 및 상위 컴포넌트 알림
  useEffect(() => {
    setFilteredLogs(logs)
    onLogsUpdate?.(logs)
  }, [logs, onLogsUpdate])

  // 자동 스크롤
  useEffect(() => {
    if (autoScrollState && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [filteredLogs, autoScrollState])

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'debug':
        return 'text-gray-600 bg-gray-50'
      case 'info':
        return 'text-blue-600 bg-blue-50'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50'
      case 'error':
        return 'text-red-600 bg-red-50'
      case 'critical':
        return 'text-red-800 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'upload':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        )
      case 'encoding':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        )
      case 'processing':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'error':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      default:
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('ko-KR', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })
  }

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-600 bg-green-100'
      case 'connecting':
        return 'text-yellow-600 bg-yellow-100'
      case 'disconnected':
        return 'text-red-600 bg-red-100'
    }
  }

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return '연결됨'
      case 'connecting':
        return '연결 중...'
      case 'disconnected':
        return '연결 끊김'
    }
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* 헤더 */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-medium text-gray-900">실시간 로그</h3>
            <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getConnectionStatusColor()}`}>
              <div className={`w-2 h-2 rounded-full mr-1 ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'}`}></div>
              {getConnectionStatusText()}
            </span>
            {chapterId && (
              <span className="text-sm text-gray-500">
                챕터: {chapterId.slice(0, 8)}...
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={`text-sm px-2 py-1 rounded ${
                showAdvancedFilters ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {showAdvancedFilters ? '간단 필터' : '고급 필터'}
            </button>
            
            <button
              onClick={clearLogs}
              className="text-sm text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
            >
              로그 지우기
            </button>
            
            {connectionStatus === 'disconnected' && (
              <button
                onClick={connect}
                className="text-sm text-blue-600 hover:text-blue-800 px-2 py-1 rounded"
              >
                다시 연결
              </button>
            )}
            
            {connectionStatus === 'connected' && (
              <button
                onClick={disconnect}
                className="text-sm text-red-600 hover:text-red-800 px-2 py-1 rounded"
              >
                연결 끊기
              </button>
            )}
          </div>
        </div>
        
        {/* 에러 표시 */}
        {error && (
          <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
      </div>

      {/* 고급 필터 */}
      {false && showAdvancedFilters && (
        <LogFilter
          logs={logs}
          onFilterChange={setFilteredLogs}
        />
      )}

      {/* 간단 검색 */}
      {false && !showAdvancedFilters && (
        <LogSearch
          logs={logs}
          onSearch={setFilteredLogs}
        />
      )}

      {/* 로그 목록 */}
      <div 
        className="overflow-y-auto"
        style={{ maxHeight }}
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm">
              {connectionStatus === 'connected' ? '아직 로그가 없습니다.' : '로그 연결을 기다리는 중...'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredLogs.map((log) => (
              <div key={log.id} className="px-4 py-2 hover:bg-gray-50">
                <div className="flex items-start space-x-3">
                  {/* 아이콘 및 레벨 */}
                  <div className={`flex-shrink-0 inline-flex items-center px-2 py-1 text-xs font-medium rounded ${getLogLevelColor(log.level)}`}>
                    {getCategoryIcon(log.category)}
                    <span className="ml-1 uppercase">{log.level}</span>
                  </div>
                  
                  {/* 메시지 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-900 font-medium">
                        {log.message}
                      </p>
                      <span className="text-xs text-gray-500 font-mono">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                    
                    {/* 컨텍스트 정보 */}
                    {(log.chapter_id || log.job_id || log.book_id) && (
                      <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
                        {log.chapter_id && (
                          <span className="bg-gray-100 px-2 py-0.5 rounded">
                            챕터: {log.chapter_id.slice(0, 8)}
                          </span>
                        )}
                        {log.job_id && (
                          <span className="bg-blue-100 px-2 py-0.5 rounded">
                            작업: {log.job_id.slice(0, 8)}
                          </span>
                        )}
                        {log.book_id && (
                          <span className="bg-green-100 px-2 py-0.5 rounded">
                            책: {log.book_id.slice(0, 8)}
                          </span>
                        )}
                      </div>
                    )}
                    
                    {/* 에러 분석 (에러 레벨인 경우) */}
                    {log.level === 'error' && (
                      <div className="mt-2">
                        <QuickErrorSolution
                          error={log.message}
                          onRetry={() => {
                            // TODO: 재시도 로직 구현
                            console.log('Retry requested for:', log.id)
                          }}
                        />
                      </div>
                    )}
                    
                    {/* 상세 정보 */}
                    {log.details && Object.keys(log.details).length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
                          상세 정보 보기
                        </summary>
                        <pre className="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>

      {/* 푸터 */}
      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>
            {filteredLogs.length !== logs.length 
              ? `${filteredLogs.length}개 표시 (전체 ${logs.length}개)`
              : `총 ${logs.length}개 로그`
            }
          </span>
          <div className="flex items-center space-x-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoScrollState}
                onChange={(e) => setAutoScrollState(e.target.checked)}
                className="mr-1"
              />
              자동 스크롤
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}

interface LogMessageItemProps {
  log: LogMessage
  showContext?: boolean
}

export function LogMessageItem({ log, showContext = true }: LogMessageItemProps) {
  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'debug':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'critical':
        return 'text-red-800 bg-red-100 border-red-300'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('ko-KR', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <div className={`border-l-4 pl-4 py-2 ${getLogLevelColor(log.level)}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{log.message}</span>
        <span className="text-xs font-mono">{formatTimestamp(log.timestamp)}</span>
      </div>
      
      {showContext && (log.chapter_id || log.job_id) && (
        <div className="mt-1 text-xs opacity-75">
          {log.chapter_id && `챕터: ${log.chapter_id.slice(0, 8)}`}
          {log.job_id && ` | 작업: ${log.job_id.slice(0, 8)}`}
        </div>
      )}
    </div>
  )
}

interface CompactLogViewerProps {
  chapterId: string
  className?: string
}

export function CompactLogViewer({ chapterId, className = '' }: CompactLogViewerProps) {
  const { logs, connectionStatus } = useWebSocketLogs({
    chapterId,
    autoConnect: true,
    maxLogHistory: 10
  })

  // 최근 5개 로그만 표시
  const recentLogs = logs.slice(-5)

  return (
    <div className={`bg-gray-50 rounded border p-3 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">최근 활동</h4>
        <div className={`w-2 h-2 rounded-full ${
          connectionStatus === 'connected' ? 'bg-green-500' : 
          connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
          'bg-red-500'
        }`} />
      </div>
      
      <div className="space-y-1">
        {recentLogs.length === 0 ? (
          <p className="text-xs text-gray-500">활동 없음</p>
        ) : (
          recentLogs.map((log) => (
            <LogMessageItem key={log.id} log={log} showContext={false} />
          ))
        )}
      </div>
    </div>
  )
}
