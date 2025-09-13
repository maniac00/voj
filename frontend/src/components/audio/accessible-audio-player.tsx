'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useAnnouncement } from '@/hooks/use-keyboard-navigation'
import { AudioPlayer } from '@/components/audio/audio-player'

interface AccessibleAudioPlayerProps {
  src: string
  title?: string
  duration?: number
  onPlay?: () => void
  onPause?: () => void
  onEnded?: () => void
  onTimeUpdate?: (currentTime: number) => void
  className?: string
}

export function AccessibleAudioPlayer({
  src,
  title = '오디오',
  duration,
  onPlay,
  onPause,
  onEnded,
  onTimeUpdate,
  className = ''
}: AccessibleAudioPlayerProps) {
  const { announce } = useAnnouncement()
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [audioDuration, setAudioDuration] = useState(duration || 0)
  const [volume, setVolume] = useState(1.0)
  const [isMuted, setIsMuted] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1.0)
  const [focusedControl, setFocusedControl] = useState<string | null>(null)

  // 음성 안내 함수들
  const announcePlayState = useCallback((playing: boolean) => {
    announce(playing ? `${title} 재생 시작` : `${title} 일시정지`)
  }, [announce, title])

  const announceTimeJump = useCallback((seconds: number, direction: 'forward' | 'backward') => {
    const directionText = direction === 'forward' ? '앞으로' : '뒤로'
    announce(`${seconds}초 ${directionText} 이동`)
  }, [announce])

  const announceVolumeChange = useCallback((newVolume: number) => {
    if (newVolume === 0) {
      announce('음소거됨')
    } else {
      announce(`볼륨 ${Math.round(newVolume * 100)}%`)
    }
  }, [announce])

  const announceSpeedChange = useCallback((speed: number) => {
    announce(`재생 속도 ${speed}배로 변경`)
  }, [announce])

  const announceTimePosition = useCallback((time: number, total: number) => {
    const currentMinutes = Math.floor(time / 60)
    const currentSeconds = Math.floor(time % 60)
    const totalMinutes = Math.floor(total / 60)
    const totalSeconds = Math.floor(total % 60)
    
    announce(
      `현재 위치: ${currentMinutes}분 ${currentSeconds}초, ` +
      `전체 ${totalMinutes}분 ${totalSeconds}초`
    )
  }, [announce])

  // 키보드 단축키 핸들러
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case ' ':
      case 'Enter':
        e.preventDefault()
        if (isPlaying) {
          setIsPlaying(false)
          onPause?.()
          announcePlayState(false)
        } else {
          setIsPlaying(true)
          onPlay?.()
          announcePlayState(true)
        }
        break
        
      case 'ArrowLeft':
        e.preventDefault()
        const newTimeBack = Math.max(0, currentTime - 10)
        setCurrentTime(newTimeBack)
        announceTimeJump(10, 'backward')
        break
        
      case 'ArrowRight':
        e.preventDefault()
        const newTimeForward = Math.min(audioDuration, currentTime + 10)
        setCurrentTime(newTimeForward)
        announceTimeJump(10, 'forward')
        break
        
      case 'ArrowUp':
        e.preventDefault()
        const newVolumeUp = Math.min(1, volume + 0.1)
        setVolume(newVolumeUp)
        announceVolumeChange(newVolumeUp)
        break
        
      case 'ArrowDown':
        e.preventDefault()
        const newVolumeDown = Math.max(0, volume - 0.1)
        setVolume(newVolumeDown)
        announceVolumeChange(newVolumeDown)
        break
        
      case 'm':
      case 'M':
        e.preventDefault()
        setIsMuted(!isMuted)
        announceVolumeChange(isMuted ? volume : 0)
        break
        
      case 'i':
      case 'I':
        e.preventDefault()
        announceTimePosition(currentTime, audioDuration)
        break
        
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
        e.preventDefault()
        const percentage = parseInt(e.key) * 0.2 // 20%, 40%, 60%, 80%, 100%
        const newTime = audioDuration * percentage
        setCurrentTime(newTime)
        announce(`${percentage * 100}% 위치로 이동`)
        break
        
      case '+':
      case '=':
        e.preventDefault()
        const fasterRate = Math.min(2.0, playbackRate + 0.25)
        setPlaybackRate(fasterRate)
        announceSpeedChange(fasterRate)
        break
        
      case '-':
        e.preventDefault()
        const slowerRate = Math.max(0.5, playbackRate - 0.25)
        setPlaybackRate(slowerRate)
        announceSpeedChange(slowerRate)
        break
        
      case '0':
        e.preventDefault()
        setPlaybackRate(1.0)
        announceSpeedChange(1.0)
        break
        
      case 'h':
      case 'H':
      case '?':
        e.preventDefault()
        announceKeyboardHelp()
        break
    }
  }, [isPlaying, currentTime, audioDuration, volume, isMuted, playbackRate, onPlay, onPause, announcePlayState, announceTimeJump, announceVolumeChange, announceSpeedChange, announceTimePosition])

  const announceKeyboardHelp = useCallback(() => {
    const helpText = [
      '키보드 단축키:',
      '스페이스바 또는 엔터: 재생 일시정지',
      '왼쪽 오른쪽 화살표: 10초 건너뛰기',
      '위 아래 화살표: 볼륨 조절',
      'M: 음소거 토글',
      'I: 현재 위치 안내',
      '1-5: 20% 단위로 위치 이동',
      '플러스 마이너스: 재생 속도 조절',
      '0: 재생 속도 초기화',
      'H 또는 물음표: 도움말'
    ].join('. ')
    
    announce(helpText)
  }, [announce])

  // 포커스 관리
  const handleFocus = useCallback((controlName: string) => {
    setFocusedControl(controlName)
    
    const controlDescriptions: Record<string, string> = {
      'play-button': '재생 일시정지 버튼',
      'progress-bar': '재생 진행률 바',
      'volume-slider': '볼륨 조절 슬라이더',
      'speed-selector': '재생 속도 선택',
      'mute-button': '음소거 버튼'
    }
    
    const description = controlDescriptions[controlName] || controlName
    announce(`${description}에 포커스됨`)
  }, [announce])

  return (
    <div 
      className={`bg-white rounded-lg border border-gray-200 p-4 focus-within:ring-2 focus-within:ring-blue-500 ${className}`}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
      role="application"
      aria-label={`${title} 오디오 플레이어`}
      aria-describedby="player-help"
    >
      {/* 숨겨진 도움말 */}
      <div id="player-help" className="sr-only">
        오디오 플레이어입니다. 스페이스바로 재생 일시정지, 화살표 키로 탐색 및 볼륨 조절, H키로 전체 도움말을 들을 수 있습니다.
      </div>

      {/* 플레이어 제목 */}
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900" id="player-title">
          {title}
        </h3>
        <div className="text-sm text-gray-600" aria-live="polite">
          {isPlaying ? '재생 중' : '일시정지됨'} • 
          재생 속도: {playbackRate}x • 
          볼륨: {isMuted ? '음소거' : `${Math.round(volume * 100)}%`}
        </div>
      </div>

      {/* 메인 컨트롤 */}
      <div className="space-y-4">
        {/* 재생/일시정지 버튼 (큰 버튼) */}
        <div className="text-center">
          <button
            onFocus={() => handleFocus('play-button')}
            className="p-4 bg-blue-600 text-white rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            aria-label={`${title} ${isPlaying ? '일시정지' : '재생'}`}
            aria-pressed={isPlaying}
          >
            {isPlaying ? (
              <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        </div>

        {/* 진행률 바 (접근성 개선) */}
        <div>
          <label htmlFor="progress-slider" className="block text-sm font-medium text-gray-700 mb-2">
            재생 위치
          </label>
          <input
            id="progress-slider"
            type="range"
            min="0"
            max={audioDuration}
            value={currentTime}
            onChange={(e) => {
              const newTime = parseFloat(e.target.value)
              setCurrentTime(newTime)
              announce(`${Math.floor(newTime / 60)}분 ${Math.floor(newTime % 60)}초로 이동`)
            }}
            onFocus={() => handleFocus('progress-bar')}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="재생 위치 조절"
            aria-valuetext={`${Math.floor(currentTime / 60)}분 ${Math.floor(currentTime % 60)}초, 전체 ${Math.floor(audioDuration / 60)}분 ${Math.floor(audioDuration % 60)}초`}
          />
          <div className="flex justify-between mt-1 text-sm text-gray-600">
            <span aria-label={`현재 시간 ${Math.floor(currentTime / 60)}분 ${Math.floor(currentTime % 60)}초`}>
              {Math.floor(currentTime / 60)}:{(Math.floor(currentTime % 60)).toString().padStart(2, '0')}
            </span>
            <span aria-label={`전체 시간 ${Math.floor(audioDuration / 60)}분 ${Math.floor(audioDuration % 60)}초`}>
              {Math.floor(audioDuration / 60)}:{(Math.floor(audioDuration % 60)).toString().padStart(2, '0')}
            </span>
          </div>
        </div>

        {/* 탐색 버튼 */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => {
              const newTime = Math.max(0, currentTime - 30)
              setCurrentTime(newTime)
              announceTimeJump(30, 'backward')
            }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            aria-label="30초 뒤로"
          >
            ⏪ 30초
          </button>
          
          <button
            onClick={() => {
              const newTime = Math.max(0, currentTime - 10)
              setCurrentTime(newTime)
              announceTimeJump(10, 'backward')
            }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            aria-label="10초 뒤로"
          >
            ⏪ 10초
          </button>
          
          <button
            onClick={() => {
              const newTime = Math.min(audioDuration, currentTime + 10)
              setCurrentTime(newTime)
              announceTimeJump(10, 'forward')
            }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            aria-label="10초 앞으로"
          >
            10초 ⏩
          </button>
          
          <button
            onClick={() => {
              const newTime = Math.min(audioDuration, currentTime + 30)
              setCurrentTime(newTime)
              announceTimeJump(30, 'forward')
            }}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
            aria-label="30초 앞으로"
          >
            30초 ⏩
          </button>
        </div>

        {/* 볼륨 조절 */}
        <div>
          <label htmlFor="volume-slider" className="block text-sm font-medium text-gray-700 mb-2">
            볼륨 조절
          </label>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                setIsMuted(!isMuted)
                announceVolumeChange(isMuted ? volume : 0)
              }}
              onFocus={() => handleFocus('mute-button')}
              className="p-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
              aria-label={isMuted ? '음소거 해제' : '음소거'}
              aria-pressed={isMuted}
            >
              {isMuted ? (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              )}
            </button>
            
            <input
              id="volume-slider"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={(e) => {
                const newVolume = parseFloat(e.target.value)
                setVolume(newVolume)
                if (newVolume > 0 && isMuted) {
                  setIsMuted(false)
                }
                announceVolumeChange(newVolume)
              }}
              onFocus={() => handleFocus('volume-slider')}
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="볼륨 조절"
              aria-valuetext={`볼륨 ${Math.round((isMuted ? 0 : volume) * 100)}%`}
            />
            
            <span className="text-sm text-gray-600 w-12 text-right" aria-live="polite">
              {Math.round((isMuted ? 0 : volume) * 100)}%
            </span>
          </div>
        </div>

        {/* 재생 속도 조절 */}
        <div>
          <label htmlFor="speed-selector" className="block text-sm font-medium text-gray-700 mb-2">
            재생 속도
          </label>
          <select
            id="speed-selector"
            value={playbackRate}
            onChange={(e) => {
              const newRate = parseFloat(e.target.value)
              setPlaybackRate(newRate)
              announceSpeedChange(newRate)
            }}
            onFocus={() => handleFocus('speed-selector')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="재생 속도 선택"
          >
            <option value="0.5">0.5배 (느리게)</option>
            <option value="0.75">0.75배</option>
            <option value="1.0">1.0배 (보통)</option>
            <option value="1.25">1.25배</option>
            <option value="1.5">1.5배</option>
            <option value="2.0">2.0배 (빠르게)</option>
          </select>
        </div>
      </div>

      {/* 키보드 단축키 안내 */}
      <details className="mt-4 border-t border-gray-200 pt-4">
        <summary className="text-sm font-medium text-gray-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
          키보드 단축키 안내
        </summary>
        <div className="mt-2 text-sm text-gray-600 space-y-1">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div><kbd className="bg-gray-100 px-1 rounded">스페이스</kbd> 재생/일시정지</div>
            <div><kbd className="bg-gray-100 px-1 rounded">←/→</kbd> 10초 건너뛰기</div>
            <div><kbd className="bg-gray-100 px-1 rounded">↑/↓</kbd> 볼륨 조절</div>
            <div><kbd className="bg-gray-100 px-1 rounded">M</kbd> 음소거 토글</div>
            <div><kbd className="bg-gray-100 px-1 rounded">I</kbd> 현재 위치 안내</div>
            <div><kbd className="bg-gray-100 px-1 rounded">1-5</kbd> 위치 이동 (20% 단위)</div>
            <div><kbd className="bg-gray-100 px-1 rounded">+/-</kbd> 재생 속도 조절</div>
            <div><kbd className="bg-gray-100 px-1 rounded">H</kbd> 도움말</div>
          </div>
        </div>
      </details>

      {/* 상태 안내 (스크린 리더용) */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {focusedControl && `${focusedControl} 컨트롤에 포커스됨`}
      </div>

      {/* 실제 AudioPlayer 컴포넌트 (숨김) */}
      <div className="sr-only">
        <AudioPlayer
          src={src}
          title={title}
          duration={duration}
          onPlay={() => {
            setIsPlaying(true)
            onPlay?.()
          }}
          onPause={() => {
            setIsPlaying(false)
            onPause?.()
          }}
          onEnded={() => {
            setIsPlaying(false)
            onEnded?.()
            announce(`${title} 재생 완료`)
          }}
          onTimeUpdate={(time) => {
            setCurrentTime(time)
            onTimeUpdate?.(time)
          }}
          onLoadedMetadata={(dur) => {
            setAudioDuration(dur)
            announce(`${title} 로드됨. 재생시간 ${Math.floor(dur / 60)}분 ${Math.floor(dur % 60)}초`)
          }}
          volume={volume}
          muted={isMuted}
        />
      </div>
    </div>
  )
}

interface AccessiblePlaylistProps {
  chapters: Array<{
    chapter_id: string
    title: string
    duration: number
    status: string
  }>
  currentChapterId?: string
  onChapterSelect: (chapterId: string) => void
  onPlay: (chapterId: string) => void
  className?: string
}

export function AccessiblePlaylist({
  chapters,
  currentChapterId,
  onChapterSelect,
  onPlay,
  className = ''
}: AccessiblePlaylistProps) {
  const { announce } = useAnnouncement()
  const [focusedIndex, setFocusedIndex] = useState(0)

  const readyChapters = chapters.filter(c => c.status === 'ready')
  const currentIndex = readyChapters.findIndex(c => c.chapter_id === currentChapterId)

  const handleKeyDown = useCallback((e: React.KeyboardEvent, index: number) => {
    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault()
        const prevIndex = Math.max(0, index - 1)
        setFocusedIndex(prevIndex)
        announce(`챕터 ${readyChapters[prevIndex].title}`)
        break
        
      case 'ArrowDown':
        e.preventDefault()
        const nextIndex = Math.min(readyChapters.length - 1, index + 1)
        setFocusedIndex(nextIndex)
        announce(`챕터 ${readyChapters[nextIndex].title}`)
        break
        
      case 'Enter':
      case ' ':
        e.preventDefault()
        const chapter = readyChapters[index]
        onChapterSelect(chapter.chapter_id)
        announce(`${chapter.title} 선택됨`)
        break
        
      case 'p':
      case 'P':
        e.preventDefault()
        const playChapter = readyChapters[index]
        onPlay(playChapter.chapter_id)
        announce(`${playChapter.title} 재생 시작`)
        break
    }
  }, [readyChapters, onChapterSelect, onPlay, announce])

  return (
    <div 
      className={`bg-white rounded-lg border border-gray-200 ${className}`}
      role="listbox"
      aria-label="챕터 플레이리스트"
    >
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">플레이리스트</h3>
        <p className="text-sm text-gray-600">
          {readyChapters.length}개 챕터 재생 가능
        </p>
      </div>

      <div className="p-4">
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {readyChapters.map((chapter, index) => (
            <div
              key={chapter.chapter_id}
              role="option"
              aria-selected={chapter.chapter_id === currentChapterId}
              tabIndex={0}
              onKeyDown={(e) => handleKeyDown(e, index)}
              onFocus={() => setFocusedIndex(index)}
              onClick={() => onChapterSelect(chapter.chapter_id)}
              className={`p-3 rounded-lg border cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                chapter.chapter_id === currentChapterId
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
              aria-label={`챕터 ${chapter.title}, ${Math.floor(chapter.duration / 60)}분 ${Math.floor(chapter.duration % 60)}초`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {chapter.title}
                  </h4>
                  <p className="text-xs text-gray-500">
                    {Math.floor(chapter.duration / 60)}분 {Math.floor(chapter.duration % 60)}초
                  </p>
                </div>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onPlay(chapter.chapter_id)
                  }}
                  className="p-1 text-green-600 hover:text-green-800 focus:outline-none focus:ring-2 focus:ring-green-500 rounded"
                  aria-label={`${chapter.title} 재생`}
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* 플레이리스트 단축키 안내 */}
        <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600">
          <p><strong>플레이리스트 단축키:</strong></p>
          <p>↑/↓: 챕터 탐색, Enter/Space: 선택, P: 재생</p>
        </div>
      </div>
    </div>
  )
}
