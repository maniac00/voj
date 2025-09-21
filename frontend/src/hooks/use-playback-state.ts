'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

export interface PlaybackState {
  chapterId: string
  currentTime: number
  duration: number
  volume: number
  playbackRate: number
  isMuted: boolean
  isPlaying: boolean
  lastUpdated: number
  bookId: string
  chapterTitle?: string
}

export interface PlaybackSettings {
  autoSave: boolean
  saveInterval: number // ms
  resumeThreshold: number // seconds
  maxSavedStates: number
}

const DEFAULT_SETTINGS: PlaybackSettings = {
  autoSave: true,
  saveInterval: 5000, // 5초마다 저장
  resumeThreshold: 10, // 10초 이상 재생했으면 저장
  maxSavedStates: 10
}

const STORAGE_KEY_PREFIX = 'voj_playback_'

export function usePlaybackState(
  chapterId: string,
  bookId: string,
  settings: Partial<PlaybackSettings> = {}
) {
  const config = { ...DEFAULT_SETTINGS, ...settings }
  const [state, setState] = useState<PlaybackState>({
    chapterId,
    currentTime: 0,
    duration: 0,
    volume: 1.0,
    playbackRate: 1.0,
    isMuted: false,
    isPlaying: false,
    lastUpdated: Date.now(),
    bookId,
    chapterTitle: ''
  })

  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastSaveTimeRef = useRef<number>(0)

  // 저장 키 생성
  const getStorageKey = useCallback((id: string) => {
    return `${STORAGE_KEY_PREFIX}${bookId}_${id}`
  }, [bookId])

  // 상태 저장
  const saveState = useCallback((stateToSave: PlaybackState) => {
    if (!config.autoSave) return

    try {
      // 최소 재생 시간 확인
      if (stateToSave.currentTime < config.resumeThreshold) {
        return
      }

      const key = getStorageKey(stateToSave.chapterId)
      localStorage.setItem(key, JSON.stringify({
        ...stateToSave,
        lastUpdated: Date.now()
      }))

      lastSaveTimeRef.current = Date.now()
      
      // 최대 저장 개수 관리
      cleanupOldStates()
      
    } catch (error) {
      console.warn('Failed to save playback state:', error)
    }
  }, [config, getStorageKey])

  // 상태 복원
  const loadState = useCallback((id: string): PlaybackState | null => {
    try {
      const key = getStorageKey(id)
      const saved = localStorage.getItem(key)
      
      if (saved) {
        const parsedState = JSON.parse(saved) as PlaybackState
        
        // 24시간 이내의 상태만 복원
        const maxAge = 24 * 60 * 60 * 1000 // 24시간
        if (Date.now() - parsedState.lastUpdated < maxAge) {
          return parsedState
        }
      }
    } catch (error) {
      console.warn('Failed to load playback state:', error)
    }
    
    return null
  }, [getStorageKey])

  // 오래된 상태 정리
  const cleanupOldStates = useCallback(() => {
    try {
      const keys = Object.keys(localStorage).filter(key => 
        key.startsWith(STORAGE_KEY_PREFIX)
      )

      if (keys.length <= config.maxSavedStates) {
        return
      }

      // 저장 시간 기준으로 정렬
      const statesWithTime = keys.map(key => {
        try {
          const data = JSON.parse(localStorage.getItem(key) || '{}')
          return { key, lastUpdated: data.lastUpdated || 0 }
        } catch {
          return { key, lastUpdated: 0 }
        }
      }).sort((a, b) => a.lastUpdated - b.lastUpdated)

      // 오래된 것부터 삭제
      const toDelete = statesWithTime.slice(0, keys.length - config.maxSavedStates)
      toDelete.forEach(({ key }) => {
        localStorage.removeItem(key)
      })

    } catch (error) {
      console.warn('Failed to cleanup old states:', error)
    }
  }, [config.maxSavedStates])

  // 상태 업데이트 함수들
  const updateCurrentTime = useCallback((time: number) => {
    setState(prev => ({ ...prev, currentTime: time, lastUpdated: Date.now() }))
  }, [])

  const updateDuration = useCallback((duration: number) => {
    setState(prev => ({ ...prev, duration, lastUpdated: Date.now() }))
  }, [])

  const updateVolume = useCallback((volume: number) => {
    setState(prev => ({ ...prev, volume, lastUpdated: Date.now() }))
  }, [])

  const updatePlaybackRate = useCallback((rate: number) => {
    setState(prev => ({ ...prev, playbackRate: rate, lastUpdated: Date.now() }))
  }, [])

  const updateMuted = useCallback((muted: boolean) => {
    setState(prev => ({ ...prev, isMuted: muted, lastUpdated: Date.now() }))
  }, [])

  const updatePlaying = useCallback((playing: boolean) => {
    setState(prev => ({ ...prev, isPlaying: playing, lastUpdated: Date.now() }))
  }, [])

  const updateChapterTitle = useCallback((title: string) => {
    setState(prev => ({ ...prev, chapterTitle: title, lastUpdated: Date.now() }))
  }, [])

  // 자동 저장
  useEffect(() => {
    if (config.autoSave && state.isPlaying) {
      // 저장 타이머 설정
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }

      saveTimeoutRef.current = setTimeout(() => {
        saveState(state)
      }, config.saveInterval)

      return () => {
        if (saveTimeoutRef.current) {
          clearTimeout(saveTimeoutRef.current)
        }
      }
    }
  }, [state, config.autoSave, config.saveInterval, saveState])

  // 페이지 언로드 시 상태 저장
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (state.isPlaying && state.currentTime > config.resumeThreshold) {
        saveState(state)
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [state, config.resumeThreshold, saveState])

  // 컴포넌트 언마운트 시 상태 저장
  useEffect(() => {
    return () => {
      if (state.currentTime > config.resumeThreshold) {
        saveState(state)
      }
    }
  }, [state, config.resumeThreshold, saveState])

  // 초기 상태 복원
  useEffect(() => {
    if (chapterId) {
      const savedState = loadState(chapterId)
      if (savedState) {
        setState(savedState)
      } else {
        setState(prev => ({ ...prev, chapterId }))
      }
    }
  }, [chapterId, loadState])

  // 수동 저장
  const manualSave = useCallback(() => {
    saveState(state)
    return true
  }, [state, saveState])

  // 상태 초기화
  const resetState = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentTime: 0,
      isPlaying: false,
      lastUpdated: Date.now()
    }))
    
    // 저장된 상태도 삭제
    try {
      const key = getStorageKey(chapterId)
      localStorage.removeItem(key)
    } catch (error) {
      console.warn('Failed to remove saved state:', error)
    }
  }, [chapterId, getStorageKey])

  // 북마크 기능
  const createBookmark = useCallback((name?: string) => {
    const bookmarkName = name || `${Math.floor(state.currentTime / 60)}분 ${Math.floor(state.currentTime % 60)}초`
    
    try {
      const bookmarksKey = `voj_bookmarks_${bookId}`
      const existingBookmarks = JSON.parse(localStorage.getItem(bookmarksKey) || '[]')
      
      const newBookmark = {
        id: Date.now().toString(),
        name: bookmarkName,
        chapterId: state.chapterId,
        currentTime: state.currentTime,
        chapterTitle: state.chapterTitle,
        createdAt: new Date().toISOString()
      }
      
      const updatedBookmarks = [...existingBookmarks, newBookmark]
      localStorage.setItem(bookmarksKey, JSON.stringify(updatedBookmarks))
      
      return newBookmark.id
    } catch (error) {
      console.warn('Failed to create bookmark:', error)
      return null
    }
  }, [state, bookId])

  // 북마크 목록 조회
  const getBookmarks = useCallback(() => {
    try {
      const bookmarksKey = `voj_bookmarks_${bookId}`
      return JSON.parse(localStorage.getItem(bookmarksKey) || '[]')
    } catch (error) {
      console.warn('Failed to get bookmarks:', error)
      return []
    }
  }, [bookId])

  // 북마크로 이동
  const goToBookmark = useCallback((bookmarkId: string) => {
    try {
      const bookmarks = getBookmarks()
      const bookmark = bookmarks.find((b: any) => b.id === bookmarkId)
      
      if (bookmark) {
        setState(prev => ({
          ...prev,
          chapterId: bookmark.chapterId,
          currentTime: bookmark.currentTime,
          chapterTitle: bookmark.chapterTitle
        }))
        return true
      }
    } catch (error) {
      console.warn('Failed to go to bookmark:', error)
    }
    
    return false
  }, [getBookmarks])

  return {
    state,
    updateCurrentTime,
    updateDuration,
    updateVolume,
    updatePlaybackRate,
    updateMuted,
    updatePlaying,
    updateChapterTitle,
    manualSave,
    resetState,
    createBookmark,
    getBookmarks,
    goToBookmark,
    config
  }
}

// 전역 재생 상태 관리 (여러 컴포넌트에서 공유)
class GlobalPlaybackManager {
  private currentState: PlaybackState | null = null
  private listeners: Set<(state: PlaybackState | null) => void> = new Set()

  setCurrentState(state: PlaybackState | null) {
    this.currentState = state
    this.notifyListeners()
  }

  getCurrentState(): PlaybackState | null {
    return this.currentState
  }

  subscribe(listener: (state: PlaybackState | null) => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notifyListeners() {
    this.listeners.forEach(listener => {
      try {
        listener(this.currentState)
      } catch (error) {
        console.warn('Playback state listener error:', error)
      }
    })
  }
}

export const globalPlaybackManager = new GlobalPlaybackManager()

// 전역 재생 상태 훅
export function useGlobalPlaybackState() {
  const [globalState, setGlobalState] = useState<PlaybackState | null>(
    globalPlaybackManager.getCurrentState()
  )

  useEffect(() => {
    const unsubscribe = globalPlaybackManager.subscribe(setGlobalState)
    return () => { unsubscribe(); }
  }, [])

  const setGlobalPlaybackState = useCallback((state: PlaybackState | null) => {
    globalPlaybackManager.setCurrentState(state)
  }, [])

  return {
    globalState,
    setGlobalPlaybackState
  }
}

// 재생 기록 관리
export interface PlaybackHistory {
  id: string
  bookId: string
  chapterId: string
  chapterTitle: string
  currentTime: number
  duration: number
  playedAt: Date
  completedPercentage: number
}

export function usePlaybackHistory(bookId: string) {
  const [history, setHistory] = useState<PlaybackHistory[]>([])

  const getHistoryKey = () => `voj_playback_history_${bookId}`

  // 기록 로드
  useEffect(() => {
    try {
      const saved = localStorage.getItem(getHistoryKey())
      if (saved) {
        const parsedHistory = JSON.parse(saved).map((item: any) => ({
          ...item,
          playedAt: new Date(item.playedAt)
        }))
        setHistory(parsedHistory)
      }
    } catch (error) {
      console.warn('Failed to load playback history:', error)
    }
  }, [bookId])

  // 재생 기록 추가
  const addToHistory = useCallback((
    chapterId: string,
    chapterTitle: string,
    currentTime: number,
    duration: number
  ) => {
    const completedPercentage = duration > 0 ? (currentTime / duration) * 100 : 0
    
    // 5% 이상 재생했을 때만 기록
    if (completedPercentage < 5) {
      return
    }

    const newRecord: PlaybackHistory = {
      id: Date.now().toString(),
      bookId,
      chapterId,
      chapterTitle,
      currentTime,
      duration,
      playedAt: new Date(),
      completedPercentage
    }

    try {
      const updatedHistory = [newRecord, ...history.filter(h => h.chapterId !== chapterId)]
        .slice(0, 50) // 최대 50개 기록 유지

      setHistory(updatedHistory)
      localStorage.setItem(getHistoryKey(), JSON.stringify(updatedHistory))
    } catch (error) {
      console.warn('Failed to add to playback history:', error)
    }
  }, [history, bookId])

  // 최근 재생 기록 조회
  const getRecentlyPlayed = useCallback((limit: number = 5) => {
    return history
      .sort((a, b) => b.playedAt.getTime() - a.playedAt.getTime())
      .slice(0, limit)
  }, [history])

  // 완료된 챕터 조회
  const getCompletedChapters = useCallback(() => {
    return history.filter(h => h.completedPercentage >= 95) // 95% 이상 재생한 챕터
  }, [history])

  // 진행 중인 챕터 조회
  const getInProgressChapters = useCallback(() => {
    return history.filter(h => h.completedPercentage >= 5 && h.completedPercentage < 95)
  }, [history])

  // 기록 삭제
  const removeFromHistory = useCallback((recordId: string) => {
    try {
      const updatedHistory = history.filter(h => h.id !== recordId)
      setHistory(updatedHistory)
      localStorage.setItem(getHistoryKey(), JSON.stringify(updatedHistory))
    } catch (error) {
      console.warn('Failed to remove from history:', error)
    }
  }, [history])

  // 전체 기록 삭제
  const clearHistory = useCallback(() => {
    try {
      setHistory([])
      localStorage.removeItem(getHistoryKey())
    } catch (error) {
      console.warn('Failed to clear history:', error)
    }
  }, [])

  return {
    history,
    addToHistory,
    getRecentlyPlayed,
    getCompletedChapters,
    getInProgressChapters,
    removeFromHistory,
    clearHistory
  }
}

// 재생 세션 관리
export interface PlaybackSession {
  id: string
  bookId: string
  startedAt: Date
  endedAt?: Date
  totalPlayTime: number
  chaptersPlayed: string[]
  lastChapterId?: string
  lastPosition?: number
}

export function usePlaybackSession(bookId: string) {
  const [currentSession, setCurrentSession] = useState<PlaybackSession | null>(null)
  const sessionStartTimeRef = useRef<number>(0)

  // 세션 시작
  const startSession = useCallback(() => {
    const session: PlaybackSession = {
      id: Date.now().toString(),
      bookId,
      startedAt: new Date(),
      totalPlayTime: 0,
      chaptersPlayed: []
    }

    setCurrentSession(session)
    sessionStartTimeRef.current = Date.now()
    
    return session.id
  }, [bookId])

  // 세션 종료
  const endSession = useCallback(() => {
    if (currentSession) {
      const endedSession: PlaybackSession = {
        ...currentSession,
        endedAt: new Date(),
        totalPlayTime: currentSession.totalPlayTime + (Date.now() - sessionStartTimeRef.current) / 1000
      }

      // 세션 기록 저장
      try {
        const sessionsKey = `voj_sessions_${bookId}`
        const existingSessions = JSON.parse(localStorage.getItem(sessionsKey) || '[]')
        const updatedSessions = [endedSession, ...existingSessions].slice(0, 20) // 최대 20개 세션 유지
        
        localStorage.setItem(sessionsKey, JSON.stringify(updatedSessions))
      } catch (error) {
        console.warn('Failed to save session:', error)
      }

      setCurrentSession(null)
      return endedSession.id
    }
    
    return null
  }, [currentSession, bookId])

  // 챕터 재생 기록
  const recordChapterPlay = useCallback((chapterId: string, position: number) => {
    if (currentSession) {
      setCurrentSession(prev => {
        if (!prev) return null
        
        return {
          ...prev,
          chaptersPlayed: [...new Set([...prev.chaptersPlayed, chapterId])],
          lastChapterId: chapterId,
          lastPosition: position
        }
      })
    }
  }, [currentSession])

  // 페이지 언로드 시 세션 종료
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (currentSession) {
        endSession()
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [currentSession, endSession])

  return {
    currentSession,
    startSession,
    endSession,
    recordChapterPlay
  }
}
