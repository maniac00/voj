'use client'

import { useState, useEffect, useCallback } from 'react'
import { LogMessage } from '@/hooks/use-websocket-logs'

export interface LogSession {
  id: string
  name: string
  startTime: Date
  endTime?: Date
  logs: LogMessage[]
  chapterId?: string
  bookId?: string
  tags: string[]
}

export interface LogExportOptions {
  format: 'json' | 'csv' | 'txt'
  includeDetails: boolean
  dateRange?: {
    start: Date
    end: Date
  }
  filters?: {
    levels: string[]
    categories: string[]
  }
}

const STORAGE_KEY = 'voj_log_sessions'
const MAX_STORED_SESSIONS = 10
const MAX_LOGS_PER_SESSION = 1000

export function useLogStorage() {
  const [sessions, setSessions] = useState<LogSession[]>([])
  const [currentSession, setCurrentSession] = useState<LogSession | null>(null)
  const [autoSave, setAutoSave] = useState(true)

  // 로컬 스토리지에서 세션 로드
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsedSessions = JSON.parse(stored).map((session: any) => ({
          ...session,
          startTime: new Date(session.startTime),
          endTime: session.endTime ? new Date(session.endTime) : undefined
        }))
        setSessions(parsedSessions)
      }
    } catch (error) {
      console.error('Failed to load log sessions:', error)
    }
  }, [])

  // 세션 저장
  const saveSessions = useCallback((sessionsToSave: LogSession[]) => {
    try {
      // 최대 개수 제한
      const limitedSessions = sessionsToSave.slice(-MAX_STORED_SESSIONS)
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(limitedSessions))
      setSessions(limitedSessions)
    } catch (error) {
      console.error('Failed to save log sessions:', error)
    }
  }, [])

  // 새 세션 시작
  const startSession = useCallback((name: string, chapterId?: string, bookId?: string) => {
    const newSession: LogSession = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      name,
      startTime: new Date(),
      logs: [],
      chapterId,
      bookId,
      tags: []
    }

    setCurrentSession(newSession)
    return newSession.id
  }, [])

  // 현재 세션 종료
  const endCurrentSession = useCallback(() => {
    if (currentSession) {
      const endedSession = {
        ...currentSession,
        endTime: new Date()
      }

      const updatedSessions = [...sessions, endedSession]
      saveSessions(updatedSessions)
      setCurrentSession(null)
      
      return endedSession.id
    }
    return null
  }, [currentSession, sessions, saveSessions])

  // 로그 추가
  const addLogToSession = useCallback((log: LogMessage) => {
    if (currentSession && autoSave) {
      setCurrentSession(prev => {
        if (!prev) return null
        
        const updatedLogs = [...prev.logs, log]
        
        // 로그 개수 제한
        if (updatedLogs.length > MAX_LOGS_PER_SESSION) {
          updatedLogs.splice(0, updatedLogs.length - MAX_LOGS_PER_SESSION)
        }
        
        return {
          ...prev,
          logs: updatedLogs
        }
      })
    }
  }, [currentSession, autoSave])

  // 세션 삭제
  const deleteSession = useCallback((sessionId: string) => {
    const updatedSessions = sessions.filter(s => s.id !== sessionId)
    saveSessions(updatedSessions)
  }, [sessions, saveSessions])

  // 세션 이름 변경
  const renameSession = useCallback((sessionId: string, newName: string) => {
    const updatedSessions = sessions.map(s => 
      s.id === sessionId ? { ...s, name: newName } : s
    )
    saveSessions(updatedSessions)
  }, [sessions, saveSessions])

  // 태그 추가
  const addTagToSession = useCallback((sessionId: string, tag: string) => {
    const updatedSessions = sessions.map(s => 
      s.id === sessionId ? { 
        ...s, 
        tags: [...new Set([...s.tags, tag])] 
      } : s
    )
    saveSessions(updatedSessions)
  }, [sessions, saveSessions])

  // 로그 내보내기
  const exportLogs = useCallback((
    logs: LogMessage[], 
    options: LogExportOptions,
    filename?: string
  ) => {
    try {
      let filteredLogs = logs

      // 날짜 범위 필터
      if (options.dateRange) {
        filteredLogs = filteredLogs.filter(log => {
          const logDate = new Date(log.timestamp)
          return logDate >= options.dateRange!.start && logDate <= options.dateRange!.end
        })
      }

      // 레벨 필터
      if (options.filters?.levels.length) {
        filteredLogs = filteredLogs.filter(log => 
          options.filters!.levels.includes(log.level)
        )
      }

      // 카테고리 필터
      if (options.filters?.categories.length) {
        filteredLogs = filteredLogs.filter(log => 
          options.filters!.categories.includes(log.category)
        )
      }

      const exportData = generateExportData(filteredLogs, options)
      const blob = new Blob([exportData.content], { type: exportData.mimeType })
      
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || `logs_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${options.format}`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      URL.revokeObjectURL(url)
      
      return true
    } catch (error) {
      console.error('Export failed:', error)
      return false
    }
  }, [])

  // 세션 내보내기
  const exportSession = useCallback((sessionId: string, options: LogExportOptions) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      const filename = `session_${session.name}_${session.id}.${options.format}`
      return exportLogs(session.logs, options, filename)
    }
    return false
  }, [sessions, exportLogs])

  // 서버에 로그 백업
  const backupToServer = useCallback(async (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (!session) return false

    try {
      const response = await fetch('/api/v1/logs/backup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('voj_access_token')}`
        },
        body: JSON.stringify({
          session_id: session.id,
          session_name: session.name,
          start_time: session.startTime.toISOString(),
          end_time: session.endTime?.toISOString(),
          chapter_id: session.chapterId,
          book_id: session.bookId,
          tags: session.tags,
          logs: session.logs
        })
      })

      return response.ok
    } catch (error) {
      console.error('Backup to server failed:', error)
      return false
    }
  }, [sessions])

  // 스토리지 정리
  const cleanupStorage = useCallback(() => {
    try {
      // 오래된 세션 제거 (30일 이상)
      const cutoffDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      const recentSessions = sessions.filter(s => s.startTime > cutoffDate)
      
      saveSessions(recentSessions)
      
      return sessions.length - recentSessions.length
    } catch (error) {
      console.error('Storage cleanup failed:', error)
      return 0
    }
  }, [sessions, saveSessions])

  return {
    sessions,
    currentSession,
    autoSave,
    setAutoSave,
    startSession,
    endCurrentSession,
    addLogToSession,
    deleteSession,
    renameSession,
    addTagToSession,
    exportLogs,
    exportSession,
    backupToServer,
    cleanupStorage
  }
}

function generateExportData(logs: LogMessage[], options: LogExportOptions): {
  content: string
  mimeType: string
} {
  switch (options.format) {
    case 'json':
      return {
        content: JSON.stringify({
          exported_at: new Date().toISOString(),
          total_logs: logs.length,
          logs: options.includeDetails ? logs : logs.map(log => ({
            timestamp: log.timestamp,
            level: log.level,
            category: log.category,
            message: log.message,
            chapter_id: log.chapter_id,
            job_id: log.job_id
          }))
        }, null, 2),
        mimeType: 'application/json'
      }

    case 'csv':
      const headers = [
        'timestamp',
        'level', 
        'category',
        'message',
        'chapter_id',
        'job_id'
      ]
      
      if (options.includeDetails) {
        headers.push('details')
      }

      const csvRows = [
        headers.join(','),
        ...logs.map(log => {
          const row = [
            log.timestamp,
            log.level,
            log.category,
            `"${log.message.replace(/"/g, '""')}"`,
            log.chapter_id || '',
            log.job_id || ''
          ]
          
          if (options.includeDetails && log.details) {
            row.push(`"${JSON.stringify(log.details).replace(/"/g, '""')}"`)
          }
          
          return row.join(',')
        })
      ]

      return {
        content: csvRows.join('\n'),
        mimeType: 'text/csv'
      }

    case 'txt':
      const textLines = logs.map(log => {
        let line = `[${log.timestamp}] ${log.level.toUpperCase()} (${log.category}): ${log.message}`
        
        if (log.chapter_id) {
          line += ` | Chapter: ${log.chapter_id}`
        }
        
        if (log.job_id) {
          line += ` | Job: ${log.job_id}`
        }
        
        if (options.includeDetails && log.details) {
          line += `\n  Details: ${JSON.stringify(log.details)}`
        }
        
        return line
      })

      return {
        content: [
          `# VOJ Audiobooks Logs Export`,
          `# Exported at: ${new Date().toISOString()}`,
          `# Total logs: ${logs.length}`,
          '',
          ...textLines
        ].join('\n'),
        mimeType: 'text/plain'
      }

    default:
      throw new Error(`Unsupported export format: ${options.format}`)
  }
}
