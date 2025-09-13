'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

export interface LogMessage {
  id: string
  timestamp: string
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  category: 'upload' | 'encoding' | 'processing' | 'system' | 'error'
  message: string
  details?: Record<string, any>
  chapter_id?: string
  book_id?: string
  job_id?: string
}

export interface ChapterStatus {
  chapter_id: string
  chapter_status: string
  chapter_title: string
  file_name?: string
  encoding_job?: {
    job_id: string
    status: string
    progress: number
    retry_count: number
    error_message?: string
  }
  metadata?: {
    duration: number
    bitrate: number
    sample_rate: number
    channels: number
    format: string
  }
  timestamp: string
}

interface UseWebSocketLogsOptions {
  chapterId?: string
  autoConnect?: boolean
  maxLogHistory?: number
}

export function useWebSocketLogs({
  chapterId,
  autoConnect = true,
  maxLogHistory = 100
}: UseWebSocketLogsOptions = {}) {
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [error, setError] = useState<string | null>(null)
  
  const websocketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000'
    const chapterParam = chapterId ? `?chapter_id=${encodeURIComponent(chapterId)}` : ''
    return `${protocol}//${host}/api/v1/ws/logs${chapterParam}`
  }, [chapterId])

  const connect = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setConnectionStatus('connecting')
    setError(null)

    try {
      const ws = new WebSocket(getWebSocketUrl())
      websocketRef.current = ws

      ws.onopen = () => {
        setConnectionStatus('connected')
        reconnectAttempts.current = 0
        console.log('WebSocket logs connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        setConnectionStatus('disconnected')
        console.log('WebSocket logs disconnected:', event.code, event.reason)
        
        // 자동 재연결 (정상 종료가 아닌 경우)
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current += 1
            connect()
          }, delay)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection error')
      }

    } catch (error) {
      setError(`Failed to connect: ${error}`)
      setConnectionStatus('disconnected')
    }
  }, [getWebSocketUrl])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (websocketRef.current) {
      websocketRef.current.close(1000, 'User disconnected')
      websocketRef.current = null
    }

    setConnectionStatus('disconnected')
  }, [])

  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'log':
        // 새 로그 메시지
        setLogs(prev => {
          const newLogs = [...prev, data.data as LogMessage]
          return newLogs.slice(-maxLogHistory)
        })
        break

      case 'history':
        // 로그 히스토리
        setLogs(data.logs as LogMessage[])
        break

      case 'connection':
        // 연결 상태
        if (data.status === 'connected') {
          setConnectionStatus('connected')
        }
        break

      case 'error':
        // 에러 메시지
        setError(data.message)
        break

      default:
        console.log('Unknown WebSocket message type:', data.type)
    }
  }, [maxLogHistory])

  const sendMessage = useCallback((message: any) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message))
    }
  }, [])

  const subscribeToChapter = useCallback((chapterId: string) => {
    sendMessage({
      type: 'subscribe',
      chapter_id: chapterId
    })
  }, [sendMessage])

  const unsubscribeFromChapter = useCallback((chapterId: string) => {
    sendMessage({
      type: 'unsubscribe',
      chapter_id: chapterId
    })
  }, [sendMessage])

  const requestHistory = useCallback((limit: number = 50) => {
    sendMessage({
      type: 'get_history',
      limit
    })
  }, [sendMessage])

  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  // 자동 연결
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  // 챕터 ID 변경 시 구독 업데이트
  useEffect(() => {
    if (connectionStatus === 'connected' && chapterId) {
      subscribeToChapter(chapterId)
    }
  }, [connectionStatus, chapterId, subscribeToChapter])

  return {
    logs,
    connectionStatus,
    error,
    connect,
    disconnect,
    subscribeToChapter,
    unsubscribeFromChapter,
    requestHistory,
    clearLogs,
    sendMessage
  }
}

interface UseChapterStatusOptions {
  chapterId: string
  autoConnect?: boolean
  pollInterval?: number
}

export function useChapterStatus({
  chapterId,
  autoConnect = true,
  pollInterval = 5000
}: UseChapterStatusOptions) {
  const [status, setStatus] = useState<ChapterStatus | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [error, setError] = useState<string | null>(null)
  
  const websocketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000'
    return `${protocol}//${host}/api/v1/ws/status/${encodeURIComponent(chapterId)}`
  }, [chapterId])

  const connect = useCallback(() => {
    if (!chapterId || websocketRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setConnectionStatus('connecting')
    setError(null)

    try {
      const ws = new WebSocket(getWebSocketUrl())
      websocketRef.current = ws

      ws.onopen = () => {
        setConnectionStatus('connected')
        console.log(`WebSocket chapter status connected: ${chapterId}`)
        
        // 현재 상태 요청
        ws.send(JSON.stringify({ type: 'get_status' }))
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'chapter_status') {
            setStatus(data as ChapterStatus)
          } else if (data.type === 'error') {
            setError(data.message)
          }
        } catch (error) {
          console.error('Failed to parse chapter status message:', error)
        }
      }

      ws.onclose = () => {
        setConnectionStatus('disconnected')
        
        // 자동 재연결
        if (autoConnect) {
          reconnectTimeoutRef.current = setTimeout(connect, 5000)
        }
      }

      ws.onerror = (error) => {
        console.error('Chapter status WebSocket error:', error)
        setError('Connection error')
      }

    } catch (error) {
      setError(`Failed to connect: ${error}`)
      setConnectionStatus('disconnected')
    }
  }, [chapterId, getWebSocketUrl, autoConnect])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (websocketRef.current) {
      websocketRef.current.close(1000, 'User disconnected')
      websocketRef.current = null
    }

    setConnectionStatus('disconnected')
  }, [])

  const requestStatus = useCallback(() => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: 'get_status' }))
    }
  }, [])

  // 자동 연결
  useEffect(() => {
    if (autoConnect && chapterId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, chapterId, connect, disconnect])

  // 폴링 백업 (WebSocket 실패 시)
  useEffect(() => {
    if (connectionStatus === 'disconnected' && chapterId && pollInterval > 0) {
      const interval = setInterval(() => {
        // HTTP API로 상태 조회 (폴백)
        fetch(`/api/v1/audio/${encodeURIComponent(chapterId.split('/')[0])}/chapters/${encodeURIComponent(chapterId)}`)
          .then(res => res.json())
          .then(data => {
            // 간단한 상태 정보만 업데이트
            setStatus(prev => prev ? { ...prev, chapter_status: data.status } : null)
          })
          .catch(() => {
            // 무시 (WebSocket이 주 연결 방법)
          })
      }, pollInterval)

      return () => clearInterval(interval)
    }
  }, [connectionStatus, chapterId, pollInterval])

  return {
    status,
    connectionStatus,
    error,
    connect,
    disconnect,
    requestStatus
  }
}
