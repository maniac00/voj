'use client'

import React, { useState } from 'react'
import { useLogStorage, LogSession, LogExportOptions } from '@/hooks/use-log-storage'
import { LogMessage } from '@/hooks/use-websocket-logs'
import { useNotification } from '@/contexts/notification-context'

interface LogManagerProps {
  currentLogs: LogMessage[]
  chapterId?: string
  className?: string
}

export function LogManager({ currentLogs, chapterId, className = '' }: LogManagerProps) {
  const {
    sessions,
    currentSession,
    autoSave,
    setAutoSave,
    startSession,
    endCurrentSession,
    deleteSession,
    renameSession,
    exportLogs,
    exportSession,
    backupToServer,
    cleanupStorage
  } = useLogStorage()

  const { success, error: showError } = useNotification()
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [exportOptions, setExportOptions] = useState<LogExportOptions>({
    format: 'json',
    includeDetails: true
  })

  const handleStartSession = () => {
    const name = prompt('세션 이름을 입력하세요:')
    if (name && name.trim()) {
      const sessionId = startSession(name.trim(), chapterId)
      success(`로그 세션 "${name}" 시작됨`)
    }
  }

  const handleEndSession = () => {
    if (currentSession) {
      const sessionId = endCurrentSession()
      if (sessionId) {
        success(`로그 세션 "${currentSession.name}" 종료됨`)
      }
    }
  }

  const handleRenameSession = (sessionId: string, currentName: string) => {
    const newName = prompt('새 이름을 입력하세요:', currentName)
    if (newName && newName.trim() && newName !== currentName) {
      renameSession(sessionId, newName.trim())
      success('세션 이름이 변경되었습니다')
    }
  }

  const handleDeleteSession = (sessionId: string, sessionName: string) => {
    if (confirm(`"${sessionName}" 세션을 삭제하시겠습니까?`)) {
      deleteSession(sessionId)
      success('세션이 삭제되었습니다')
    }
  }

  const handleExportCurrentLogs = () => {
    const ok = exportLogs(currentLogs, exportOptions)
    if (ok) {
      success('로그가 성공적으로 내보내졌습니다')
    } else {
      showError('로그 내보내기에 실패했습니다')
    }
    setShowExportDialog(false)
  }

  const handleExportSession = (sessionId: string) => {
    const ok = exportSession(sessionId, exportOptions)
    if (ok) {
      success('세션이 성공적으로 내보내졌습니다')
    } else {
      showError('세션 내보내기에 실패했습니다')
    }
  }

  const handleBackupToServer = async (sessionId: string) => {
    const ok = await backupToServer(sessionId)
    if (ok) {
      success('서버 백업이 완료되었습니다')
    } else {
      showError('서버 백업에 실패했습니다')
    }
  }

  const handleCleanupStorage = () => {
    if (confirm('오래된 로그 세션을 정리하시겠습니까? (30일 이상된 세션 삭제)')) {
      const removedCount = cleanupStorage()
      success(`${removedCount}개의 오래된 세션이 삭제되었습니다`)
    }
  }

  const formatDuration = (start: Date, end?: Date) => {
    const endTime = end || new Date()
    const duration = Math.floor((endTime.getTime() - start.getTime()) / 1000)
    
    const hours = Math.floor(duration / 3600)
    const minutes = Math.floor((duration % 3600) / 60)
    const seconds = duration % 60

    if (hours > 0) {
      return `${hours}시간 ${minutes}분`
    } else if (minutes > 0) {
      return `${minutes}분 ${seconds}초`
    } else {
      return `${seconds}초`
    }
  }

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">로그 관리</h3>
          <div className="flex items-center space-x-2">
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={autoSave}
                onChange={(e) => setAutoSave(e.target.checked)}
                className="mr-1 h-4 w-4 text-black focus:ring-black border-gray-300 rounded"
              />
              자동 저장
            </label>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 현재 세션 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">현재 세션</h4>
          {currentSession ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-green-800">
                    {currentSession.name}
                  </div>
                  <div className="text-xs text-green-600">
                    {formatDuration(currentSession.startTime)} 경과 | {currentSession.logs.length}개 로그
                  </div>
                </div>
                <button
                  onClick={handleEndSession}
                  className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded hover:bg-green-200"
                >
                  세션 종료
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  활성 세션이 없습니다
                </div>
                <button
                  onClick={handleStartSession}
                  className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200"
                >
                  세션 시작
                </button>
              </div>
            </div>
          )}
        </div>

        {/* 현재 로그 내보내기 */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">현재 로그 내보내기</h4>
          <div className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="text-sm text-gray-600">
              {currentLogs.length}개 로그
            </div>
            <button
              onClick={() => setShowExportDialog(true)}
              className="text-sm bg-gray-100 text-gray-700 px-3 py-1 rounded hover:bg-gray-200"
            >
              내보내기
            </button>
          </div>
        </div>

        {/* 저장된 세션 목록 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-700">저장된 세션</h4>
            <button
              onClick={handleCleanupStorage}
              className="text-xs text-gray-600 hover:text-gray-800"
            >
              정리
            </button>
          </div>
          
          {sessions.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-4">
              저장된 세션이 없습니다
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {sessions.map((session) => (
                <div key={session.id} className="border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {session.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {session.startTime.toLocaleDateString('ko-KR')} | 
                        {formatDuration(session.startTime, session.endTime)} | 
                        {session.logs.length}개 로그
                      </div>
                      {session.tags.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1">
                          {session.tags.map(tag => (
                            <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center space-x-1 ml-2">
                      <button
                        onClick={() => handleExportSession(session.id)}
                        className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded"
                        title="내보내기"
                      >
                        📤
                      </button>
                      
                      <button
                        onClick={() => handleBackupToServer(session.id)}
                        className="text-xs text-green-600 hover:text-green-800 px-2 py-1 rounded"
                        title="서버 백업"
                      >
                        ☁️
                      </button>
                      
                      <button
                        onClick={() => handleRenameSession(session.id, session.name)}
                        className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
                        title="이름 변경"
                      >
                        ✏️
                      </button>
                      
                      <button
                        onClick={() => handleDeleteSession(session.id, session.name)}
                        className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded"
                        title="삭제"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 내보내기 다이얼로그 */}
      {showExportDialog && (
        <ExportDialog
          isOpen={showExportDialog}
          onClose={() => setShowExportDialog(false)}
          onExport={handleExportCurrentLogs}
          options={exportOptions}
          onOptionsChange={setExportOptions}
          logCount={currentLogs.length}
        />
      )}
    </div>
  )
}

interface ExportDialogProps {
  isOpen: boolean
  onClose: () => void
  onExport: () => void
  options: LogExportOptions
  onOptionsChange: (options: LogExportOptions) => void
  logCount: number
}

function ExportDialog({
  isOpen,
  onClose,
  onExport,
  options,
  onOptionsChange,
  logCount
}: ExportDialogProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">로그 내보내기</h3>
          
          <div className="space-y-4">
            {/* 형식 선택 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                내보내기 형식
              </label>
              <select
                value={options.format}
                onChange={(e) => onOptionsChange({
                  ...options,
                  format: e.target.value as 'json' | 'csv' | 'txt'
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black"
              >
                <option value="json">JSON (개발자용)</option>
                <option value="csv">CSV (스프레드시트)</option>
                <option value="txt">텍스트 (사람이 읽기 쉬운)</option>
              </select>
            </div>

            {/* 옵션 */}
            <div>
              <label className="flex items-center text-sm">
                <input
                  type="checkbox"
                  checked={options.includeDetails}
                  onChange={(e) => onOptionsChange({
                    ...options,
                    includeDetails: e.target.checked
                  })}
                  className="mr-2 h-4 w-4 text-black focus:ring-black border-gray-300 rounded"
                />
                상세 정보 포함
              </label>
            </div>

            {/* 통계 */}
            <div className="bg-gray-50 rounded p-3 text-sm text-gray-600">
              <div>내보낼 로그: {logCount}개</div>
              <div>예상 파일 크기: {estimateFileSize(logCount, options.format)}KB</div>
            </div>
          </div>

          {/* 버튼 */}
          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              취소
            </button>
            <button
              onClick={onExport}
              className="px-4 py-2 text-sm font-medium text-white bg-black border border-transparent rounded-md hover:bg-gray-800"
            >
              내보내기
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function estimateFileSize(logCount: number, format: string): number {
  // 대략적인 파일 크기 추정 (KB)
  switch (format) {
    case 'json':
      return Math.round(logCount * 0.5) // 로그당 약 0.5KB
    case 'csv':
      return Math.round(logCount * 0.2) // 로그당 약 0.2KB
    case 'txt':
      return Math.round(logCount * 0.3) // 로그당 약 0.3KB
    default:
      return 0
  }
}

interface LogSessionViewerProps {
  session: LogSession
  onExport: (sessionId: string) => void
  onBackup: (sessionId: string) => void
  onDelete: (sessionId: string) => void
  onRename: (sessionId: string, currentName: string) => void
}

export function LogSessionViewer({
  session,
  onExport,
  onBackup,
  onDelete,
  onRename
}: LogSessionViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const formatDuration = (start: Date, end?: Date) => {
    const endTime = end || new Date()
    const duration = Math.floor((endTime.getTime() - start.getTime()) / 1000)
    const hours = Math.floor(duration / 3600)
    const minutes = Math.floor((duration % 3600) / 60)
    const seconds = duration % 60
    if (hours > 0) return `${hours}시간 ${minutes}분`
    if (minutes > 0) return `${minutes}분 ${seconds}초`
    return `${seconds}초`
  }

  const getLogStats = () => {
    const stats = session.logs.reduce((acc, log) => {
      acc[log.level] = (acc[log.level] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return stats
  }

  const stats = getLogStats()

  return (
    <div className="border border-gray-200 rounded-lg">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-gray-900 truncate">
              {session.name}
            </h4>
            <div className="text-xs text-gray-500 mt-1">
              {session.startTime.toLocaleString('ko-KR')}
              {session.endTime && ` - ${session.endTime.toLocaleString('ko-KR')}`}
            </div>
            <div className="text-xs text-gray-500">
              {session.logs.length}개 로그 | 
              {session.endTime ? formatDuration(session.startTime, session.endTime) : '진행 중'}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-sm text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
            >
              {isExpanded ? '접기' : '펼치기'}
            </button>
          </div>
        </div>

        {/* 확장된 내용 */}
        {isExpanded && (
          <div className="mt-4 space-y-3">
            {/* 로그 통계 */}
            <div className="bg-gray-50 rounded p-3">
              <h5 className="text-xs font-medium text-gray-700 mb-2">로그 통계</h5>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {Object.entries(stats).map(([level, count]) => (
                  <div key={level} className="flex justify-between">
                    <span className={`uppercase ${
                      level === 'error' ? 'text-red-600' :
                      level === 'warning' ? 'text-yellow-600' :
                      level === 'info' ? 'text-blue-600' :
                      'text-gray-600'
                    }`}>
                      {level}
                    </span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 태그 */}
            {session.tags.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-gray-700 mb-1">태그</h5>
                <div className="flex flex-wrap gap-1">
                  {session.tags.map(tag => (
                    <span key={tag} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 작업 버튼 */}
            <div className="flex justify-end space-x-2 pt-2 border-t border-gray-200">
              <button
                onClick={() => onExport(session.id)}
                className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded"
              >
                내보내기
              </button>
              
              <button
                onClick={() => onBackup(session.id)}
                className="text-xs text-green-600 hover:text-green-800 px-2 py-1 rounded"
              >
                서버 백업
              </button>
              
              <button
                onClick={() => onRename(session.id, session.name)}
                className="text-xs text-gray-600 hover:text-gray-800 px-2 py-1 rounded"
              >
                이름 변경
              </button>
              
              <button
                onClick={() => onDelete(session.id)}
                className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded"
              >
                삭제
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
