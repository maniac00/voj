'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useKeyboardNavigation } from '@/hooks/use-keyboard-navigation'

export interface AudioPlayerProps {
  src: string
  title?: string
  duration?: number
  onPlay?: () => void
  onPause?: () => void
  onEnded?: () => void
  onTimeUpdate?: (currentTime: number) => void
  onLoadedMetadata?: (duration: number) => void
  onError?: (error: string) => void
  autoPlay?: boolean
  loop?: boolean
  muted?: boolean
  volume?: number
  className?: string
}

export function AudioPlayer({
  src,
  title = '오디오',
  duration,
  onPlay,
  onPause,
  onEnded,
  onTimeUpdate,
  onLoadedMetadata,
  onError,
  autoPlay = false,
  loop = false,
  muted = false,
  volume = 1.0,
  className = ''
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const progressRef = useRef<HTMLDivElement>(null)
  
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [audioDuration, setAudioDuration] = useState(duration || 0)
  const [audioVolume, setAudioVolume] = useState(volume)
  const [isMuted, setIsMuted] = useState(muted)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [playbackRate, setPlaybackRate] = useState(1.0)

  // 키보드 제어
  useKeyboardNavigation({
    onEnter: () => {
      if (audioRef.current) {
        togglePlayPause()
      }
    },
    onArrowLeft: () => {
      if (audioRef.current) {
        seek(Math.max(0, currentTime - 10))
      }
    },
    onArrowRight: () => {
      if (audioRef.current) {
        seek(Math.min(audioDuration, currentTime + 10))
      }
    }
  })

  // 오디오 이벤트 핸들러
  const handleLoadStart = () => {
    setIsLoading(true)
    setError(null)
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      const duration = audioRef.current.duration
      setAudioDuration(duration)
      onLoadedMetadata?.(duration)
    }
    setIsLoading(false)
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const current = audioRef.current.currentTime
      setCurrentTime(current)
      onTimeUpdate?.(current)
    }
  }

  const handlePlay = () => {
    setIsPlaying(true)
    onPlay?.()
  }

  const handlePause = () => {
    setIsPlaying(false)
    onPause?.()
  }

  const handleEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
    onEnded?.()
  }

  const handleError = (e: React.SyntheticEvent<HTMLAudioElement, Event>) => {
    const audio = e.currentTarget
    let errorMessage = '오디오 재생 중 오류가 발생했습니다.'
    
    if (audio.error) {
      switch (audio.error.code) {
        case MediaError.MEDIA_ERR_ABORTED:
          errorMessage = '재생이 중단되었습니다.'
          break
        case MediaError.MEDIA_ERR_NETWORK:
          errorMessage = '네트워크 오류로 재생할 수 없습니다.'
          break
        case MediaError.MEDIA_ERR_DECODE:
          errorMessage = '오디오 파일을 디코딩할 수 없습니다.'
          break
        case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
          errorMessage = '지원되지 않는 오디오 형식입니다.'
          break
      }
    }
    
    setError(errorMessage)
    setIsLoading(false)
    onError?.(errorMessage)
  }

  // 재생/일시정지 토글
  const togglePlayPause = useCallback(() => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play().catch(e => {
          handleError(e as any)
        })
      }
    }
  }, [isPlaying])

  // 시간 이동
  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(time, audioDuration))
    }
  }, [audioDuration])

  // 볼륨 조절
  const setVolume = useCallback((newVolume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, newVolume))
    setAudioVolume(clampedVolume)
    
    if (audioRef.current) {
      audioRef.current.volume = clampedVolume
    }
  }, [])

  // 음소거 토글
  const toggleMute = useCallback(() => {
    setIsMuted(!isMuted)
    
    if (audioRef.current) {
      audioRef.current.muted = !isMuted
    }
  }, [isMuted])

  // 재생 속도 변경
  const changePlaybackRate = useCallback((rate: number) => {
    setPlaybackRate(rate)
    
    if (audioRef.current) {
      audioRef.current.playbackRate = rate
    }
  }, [])

  // 진행률 클릭 핸들러
  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (progressRef.current && audioDuration > 0) {
      const rect = progressRef.current.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const percentage = clickX / rect.width
      const newTime = percentage * audioDuration
      seek(newTime)
    }
  }

  // 시간 포맷팅
  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return '0:00'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`
    }
  }

  // 진행률 계산
  const progress = audioDuration > 0 ? (currentTime / audioDuration) * 100 : 0

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      {/* 숨겨진 오디오 요소 */}
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onLoadStart={handleLoadStart}
        onLoadedMetadata={handleLoadedMetadata}
        onTimeUpdate={handleTimeUpdate}
        onPlay={handlePlay}
        onPause={handlePause}
        onEnded={handleEnded}
        onError={handleError}
        loop={loop}
        muted={isMuted}
        style={{ display: 'none' }}
      />

      {/* 플레이어 헤더 */}
      <div className="mb-4">
        <h3 className="text-lg font-medium text-gray-900 truncate" title={title}>
          {title}
        </h3>
        {error && (
          <div className="mt-1 text-sm text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
      </div>

      {/* 진행률 바 */}
      <div className="mb-4">
        <div
          ref={progressRef}
          className="w-full h-2 bg-gray-200 rounded-full cursor-pointer hover:bg-gray-300 transition-colors"
          onClick={handleProgressClick}
          role="slider"
          aria-label="재생 진행률"
          aria-valuemin={0}
          aria-valuemax={audioDuration}
          aria-valuenow={currentTime}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'ArrowLeft') {
              e.preventDefault()
              seek(Math.max(0, currentTime - 5))
            } else if (e.key === 'ArrowRight') {
              e.preventDefault()
              seek(Math.min(audioDuration, currentTime + 5))
            }
          }}
        >
          <div 
            className="h-full bg-blue-500 rounded-full transition-all duration-100 ease-linear"
            style={{ width: `${progress}%` }}
          />
          
          {/* 재생 위치 핸들 */}
          <div 
            className="absolute w-4 h-4 bg-blue-600 rounded-full shadow-md transform -translate-y-1 -translate-x-2 opacity-0 hover:opacity-100 transition-opacity"
            style={{ 
              left: `${progress}%`,
              top: '50%'
            }}
          />
        </div>
        
        {/* 시간 표시 */}
        <div className="flex justify-between mt-1 text-sm text-gray-600">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(audioDuration)}</span>
        </div>
      </div>

      {/* 컨트롤 버튼 */}
      <div className="flex items-center justify-center space-x-4 mb-4">
        {/* 10초 뒤로 */}
        <button
          onClick={() => seek(Math.max(0, currentTime - 10))}
          className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-black"
          aria-label="10초 뒤로"
          disabled={isLoading}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8L12.066 11.2zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8L4.066 11.2z" />
          </svg>
        </button>

        {/* 재생/일시정지 */}
        <button
          onClick={togglePlayPause}
          className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          aria-label={isPlaying ? '일시정지' : '재생'}
          disabled={isLoading || !!error}
        >
          {isLoading ? (
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
          ) : isPlaying ? (
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          )}
        </button>

        {/* 10초 앞으로 */}
        <button
          onClick={() => seek(Math.min(audioDuration, currentTime + 10))}
          className="p-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-black"
          aria-label="10초 앞으로"
          disabled={isLoading}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" />
          </svg>
        </button>
      </div>

      {/* 하단 컨트롤 */}
      <div className="flex items-center justify-between">
        {/* 볼륨 컨트롤 */}
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMute}
            className="p-1 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-black rounded"
            aria-label={isMuted ? '음소거 해제' : '음소거'}
          >
            {isMuted || audioVolume === 0 ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            ) : audioVolume < 0.5 ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            ) : (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            )}
          </button>
          
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={isMuted ? 0 : audioVolume}
            onChange={(e) => {
              const newVolume = parseFloat(e.target.value)
              setVolume(newVolume)
              if (newVolume > 0 && isMuted) {
                setIsMuted(false)
              }
            }}
            className="w-20 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            aria-label="볼륨 조절"
          />
          
          <span className="text-xs text-gray-500 w-8">
            {Math.round((isMuted ? 0 : audioVolume) * 100)}%
          </span>
        </div>

        {/* 재생 속도 */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-600">속도:</span>
          <select
            value={playbackRate}
            onChange={(e) => changePlaybackRate(parseFloat(e.target.value))}
            className="text-xs border border-gray-300 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-black"
            aria-label="재생 속도"
          >
            <option value="0.5">0.5x</option>
            <option value="0.75">0.75x</option>
            <option value="1.0">1.0x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="2.0">2.0x</option>
          </select>
        </div>
      </div>

      {/* 키보드 단축키 안내 */}
      <div className="mt-3 text-xs text-gray-500 text-center">
        <details>
          <summary className="cursor-pointer hover:text-gray-700">키보드 단축키</summary>
          <div className="mt-1 space-y-1 text-left">
            <div>스페이스바 또는 Enter: 재생/일시정지</div>
            <div>←: 10초 뒤로</div>
            <div>→: 10초 앞으로</div>
            <div>M: 음소거 토글</div>
          </div>
        </details>
      </div>
    </div>
  )
}

interface MiniAudioPlayerProps {
  src: string
  title?: string
  onPlay?: () => void
  className?: string
}

export function MiniAudioPlayer({ src, title, onPlay, className = '' }: MiniAudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play().catch(e => {
          setError('재생할 수 없습니다')
        })
        onPlay?.()
      }
    }
  }

  return (
    <div className={`inline-flex items-center space-x-2 ${className}`}>
      <audio
        ref={audioRef}
        src={src}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onError={() => setError('재생 오류')}
        style={{ display: 'none' }}
      />
      
      <button
        onClick={togglePlay}
        className="p-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-black"
        aria-label={`${title} ${isPlaying ? '일시정지' : '재생'}`}
        disabled={!!error}
        title={error || (isPlaying ? '일시정지' : '재생')}
      >
        {isPlaying ? (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
        )}
      </button>
      
      {error && (
        <span className="text-xs text-red-600" title={error}>
          ⚠️
        </span>
      )}
    </div>
  )
}
