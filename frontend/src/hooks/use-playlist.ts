'use client'

import { useState, useEffect, useCallback } from 'react'
import { ChapterDto } from '@/lib/audio'

export interface PlaylistItem {
  chapter_id: string
  title: string
  duration: number
  file_name: string
  chapter_number: number
  status: string
}

export interface PlaylistState {
  items: PlaylistItem[]
  currentIndex: number
  isPlaying: boolean
  currentTime: number
  totalDuration: number
  playedDuration: number
  shuffle: boolean
  repeat: 'none' | 'one' | 'all'
  autoAdvance: boolean
}

interface UsePlaylistOptions {
  autoAdvance?: boolean
  shuffle?: boolean
  repeat?: 'none' | 'one' | 'all'
  onChapterChange?: (chapterId: string) => void
  onPlaylistEnd?: () => void
}

export function usePlaylist({
  autoAdvance = true,
  shuffle = false,
  repeat = 'none',
  onChapterChange,
  onPlaylistEnd
}: UsePlaylistOptions = {}) {
  const [state, setState] = useState<PlaylistState>({
    items: [],
    currentIndex: 0,
    isPlaying: false,
    currentTime: 0,
    totalDuration: 0,
    playedDuration: 0,
    shuffle,
    repeat,
    autoAdvance
  })

  const [playOrder, setPlayOrder] = useState<number[]>([])

  // 재생 순서 생성
  useEffect(() => {
    if (state.items.length === 0) {
      setPlayOrder([])
      return
    }

    if (state.shuffle) {
      // 셔플 순서 생성
      const indices = Array.from({ length: state.items.length }, (_, i) => i)
      const shuffled = [...indices].sort(() => Math.random() - 0.5)
      setPlayOrder(shuffled)
    } else {
      // 순차 재생
      const sequential = Array.from({ length: state.items.length }, (_, i) => i)
      setPlayOrder(sequential)
    }
  }, [state.items, state.shuffle])

  // 총 재생시간 계산
  useEffect(() => {
    const total = state.items.reduce((sum, item) => sum + item.duration, 0)
    setState(prev => ({ ...prev, totalDuration: total }))
  }, [state.items])

  // 플레이리스트 설정
  const setPlaylist = useCallback((chapters: ChapterDto[]) => {
    const readyChapters = chapters
      .filter(c => c.status === 'ready')
      .sort((a, b) => a.chapter_number - b.chapter_number)

    const items: PlaylistItem[] = readyChapters.map(chapter => ({
      chapter_id: chapter.chapter_id,
      title: chapter.title,
      duration: chapter.duration,
      file_name: chapter.file_name,
      chapter_number: chapter.chapter_number,
      status: chapter.status
    }))

    setState(prev => ({
      ...prev,
      items,
      currentIndex: 0,
      playedDuration: 0
    }))
  }, [])

  // 현재 챕터 조회
  const getCurrentChapter = useCallback(() => {
    if (state.items.length === 0 || playOrder.length === 0) return null
    
    const actualIndex = playOrder[state.currentIndex]
    return state.items[actualIndex] || null
  }, [state.items, state.currentIndex, playOrder])

  // 다음 챕터로 이동
  const nextChapter = useCallback(() => {
    if (state.items.length === 0) return false

    const currentChapter = getCurrentChapter()
    if (currentChapter) {
      setState(prev => ({
        ...prev,
        playedDuration: prev.playedDuration + currentChapter.duration
      }))
    }

    if (state.currentIndex < playOrder.length - 1) {
      const newIndex = state.currentIndex + 1
      setState(prev => ({ ...prev, currentIndex: newIndex }))
      
      const nextChapter = state.items[playOrder[newIndex]]
      onChapterChange?.(nextChapter.chapter_id)
      return true
    } else if (state.repeat === 'all') {
      // 전체 반복
      setState(prev => ({ ...prev, currentIndex: 0, playedDuration: 0 }))
      
      const firstChapter = state.items[playOrder[0]]
      onChapterChange?.(firstChapter.chapter_id)
      return true
    } else {
      // 플레이리스트 끝
      setState(prev => ({ ...prev, isPlaying: false }))
      onPlaylistEnd?.()
      return false
    }
  }, [state, playOrder, getCurrentChapter, onChapterChange, onPlaylistEnd])

  // 이전 챕터로 이동
  const previousChapter = useCallback(() => {
    if (state.items.length === 0) return false

    if (state.currentIndex > 0) {
      const newIndex = state.currentIndex - 1
      setState(prev => ({ ...prev, currentIndex: newIndex }))
      
      const prevChapter = state.items[playOrder[newIndex]]
      onChapterChange?.(prevChapter.chapter_id)
      return true
    } else if (state.repeat === 'all') {
      // 전체 반복 - 마지막 챕터로
      const lastIndex = playOrder.length - 1
      setState(prev => ({ ...prev, currentIndex: lastIndex }))
      
      const lastChapter = state.items[playOrder[lastIndex]]
      onChapterChange?.(lastChapter.chapter_id)
      return true
    }

    return false
  }, [state, playOrder, onChapterChange])

  // 특정 챕터로 이동
  const goToChapter = useCallback((chapterId: string) => {
    const itemIndex = state.items.findIndex(item => item.chapter_id === chapterId)
    if (itemIndex === -1) return false

    const playOrderIndex = playOrder.findIndex(index => index === itemIndex)
    if (playOrderIndex === -1) return false

    setState(prev => ({ ...prev, currentIndex: playOrderIndex }))
    onChapterChange?.(chapterId)
    return true
  }, [state.items, playOrder, onChapterChange])

  // 재생 상태 업데이트
  const setPlaying = useCallback((playing: boolean) => {
    setState(prev => ({ ...prev, isPlaying: playing }))
  }, [])

  // 현재 시간 업데이트
  const setCurrentTime = useCallback((time: number) => {
    setState(prev => ({ ...prev, currentTime: time }))
  }, [])

  // 셔플 토글
  const toggleShuffle = useCallback(() => {
    setState(prev => ({ ...prev, shuffle: !prev.shuffle }))
  }, [])

  // 반복 모드 변경
  const cycleRepeat = useCallback(() => {
    const modes: Array<'none' | 'one' | 'all'> = ['none', 'one', 'all']
    const currentModeIndex = modes.indexOf(state.repeat)
    const nextMode = modes[(currentModeIndex + 1) % modes.length]
    
    setState(prev => ({ ...prev, repeat: nextMode }))
    return nextMode
  }, [state.repeat])

  // 자동 진행 토글
  const toggleAutoAdvance = useCallback(() => {
    setState(prev => ({ ...prev, autoAdvance: !prev.autoAdvance }))
  }, [])

  // 챕터 완료 처리
  const handleChapterEnd = useCallback(() => {
    if (state.repeat === 'one') {
      // 현재 챕터 반복
      setState(prev => ({ ...prev, currentTime: 0 }))
      return
    }

    if (state.autoAdvance) {
      nextChapter()
    } else {
      setState(prev => ({ ...prev, isPlaying: false }))
    }
  }, [state.repeat, state.autoAdvance, nextChapter])

  // 플레이리스트 통계
  const getPlaylistStats = useCallback(() => {
    const currentChapter = getCurrentChapter()
    const totalProgress = state.totalDuration > 0 
      ? (state.playedDuration + state.currentTime) / state.totalDuration 
      : 0

    return {
      totalChapters: state.items.length,
      currentChapterIndex: state.currentIndex + 1,
      totalDuration: state.totalDuration,
      playedDuration: state.playedDuration + state.currentTime,
      remainingDuration: state.totalDuration - (state.playedDuration + state.currentTime),
      totalProgress: Math.min(1, totalProgress),
      currentChapter,
      estimatedTimeToEnd: currentChapter 
        ? (currentChapter.duration - state.currentTime) + 
          state.items.slice(playOrder.indexOf(state.currentIndex) + 1)
            .reduce((sum, item) => sum + item.duration, 0)
        : 0
    }
  }, [state, getCurrentChapter, playOrder])

  return {
    state,
    playOrder,
    setPlaylist,
    getCurrentChapter,
    nextChapter,
    previousChapter,
    goToChapter,
    setPlaying,
    setCurrentTime,
    toggleShuffle,
    cycleRepeat,
    toggleAutoAdvance,
    handleChapterEnd,
    getPlaylistStats
  }
}

// 플레이리스트 저장/복원을 위한 유틸리티
export function savePlaylistState(bookId: string, state: PlaylistState): void {
  try {
    const key = `voj_playlist_${bookId}`
    const stateToSave = {
      ...state,
      // 민감한 정보는 제외하고 저장
      items: state.items.map(item => ({
        chapter_id: item.chapter_id,
        title: item.title,
        duration: item.duration,
        chapter_number: item.chapter_number
      }))
    }
    
    localStorage.setItem(key, JSON.stringify(stateToSave))
  } catch (error) {
    console.warn('Failed to save playlist state:', error)
  }
}

export function loadPlaylistState(bookId: string): Partial<PlaylistState> | null {
  try {
    const key = `voj_playlist_${bookId}`
    const saved = localStorage.getItem(key)
    
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (error) {
    console.warn('Failed to load playlist state:', error)
  }
  
  return null
}

export function clearPlaylistState(bookId: string): void {
  try {
    const key = `voj_playlist_${bookId}`
    localStorage.removeItem(key)
  } catch (error) {
    console.warn('Failed to clear playlist state:', error)
  }
}
