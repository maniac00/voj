'use client'

import React, { useState, useEffect } from 'react'
import { ChapterDto } from '@/lib/audio'

interface AudioMetadata {
  duration: number
  bitrate: number
  sample_rate: number
  channels: number
  format: string
  file_size?: number
  estimated_quality?: 'low' | 'medium' | 'high' | 'excellent'
}

interface AudioMetadataDisplayProps {
  metadata: AudioMetadata
  isProcessing?: boolean
  showTechnicalDetails?: boolean
  showComparison?: boolean
  originalMetadata?: AudioMetadata
  className?: string
}

export function AudioMetadataDisplay({
  metadata,
  isProcessing = false,
  showTechnicalDetails = false,
  showComparison = false,
  originalMetadata,
  className = ''
}: AudioMetadataDisplayProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(section)) {
        newSet.delete(section)
      } else {
        newSet.add(section)
      }
      return newSet
    })
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}시간 ${minutes}분 ${secs}초`
    } else if (minutes > 0) {
      return `${minutes}분 ${secs}초`
    } else {
      return `${secs}초`
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const getQualityInfo = (bitrate: number, channels: number) => {
    if (bitrate >= 320) return { level: 'excellent', text: '최고 품질', color: 'text-green-600' }
    if (bitrate >= 192) return { level: 'high', text: '고품질', color: 'text-blue-600' }
    if (bitrate >= 128) return { level: 'medium', text: '중간 품질', color: 'text-yellow-600' }
    if (bitrate >= 64) return { level: 'medium', text: '표준 품질', color: 'text-gray-600' }
    return { level: 'low', text: '저품질', color: 'text-red-600' }
  }

  const getChannelText = (channels: number) => {
    switch (channels) {
      case 1: return '모노'
      case 2: return '스테레오'
      default: return `${channels}채널`
    }
  }

  const getFormatInfo = (format: string) => {
    const formatMap: Record<string, { name: string; description: string }> = {
      'mp3': { name: 'MP3', description: '손실 압축 (호환성 우수)' },
      'aac': { name: 'AAC', description: '고효율 압축 (스트리밍 최적화)' },
      'm4a': { name: 'M4A', description: 'AAC 컨테이너 (Apple 표준)' },
      'wav': { name: 'WAV', description: '무손실 (원본 품질)' },
      'flac': { name: 'FLAC', description: '무손실 압축' }
    }
    
    return formatMap[format.toLowerCase()] || { name: format.toUpperCase(), description: '알 수 없는 형식' }
  }

  const calculateBitrate = (fileSize: number, duration: number) => {
    if (duration === 0) return 0
    return Math.round((fileSize * 8) / (duration * 1000)) // kbps
  }

  const quality = getQualityInfo(metadata.bitrate, metadata.channels)
  const formatInfo = getFormatInfo(metadata.format)

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">오디오 메타데이터</h3>
          {isProcessing && (
            <div className="flex items-center space-x-2 text-sm text-yellow-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
              <span>분석 중...</span>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 기본 정보 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {formatDuration(metadata.duration)}
              </div>
              <div className="text-sm text-gray-600">재생시간</div>
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {metadata.bitrate}
                <span className="text-sm text-gray-600 ml-1">kbps</span>
              </div>
              <div className={`text-sm ${quality.color}`}>{quality.text}</div>
            </div>
          </div>
        </div>

        {/* 상세 정보 */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">형식</span>
            <div className="text-right">
              <span className="text-sm font-medium">{formatInfo.name}</span>
              <div className="text-xs text-gray-500">{formatInfo.description}</div>
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">채널</span>
            <span className="text-sm font-medium">{getChannelText(metadata.channels)}</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">샘플레이트</span>
            <span className="text-sm font-medium">{metadata.sample_rate.toLocaleString()} Hz</span>
          </div>
          
          {metadata.file_size && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">파일 크기</span>
              <span className="text-sm font-medium">{formatFileSize(metadata.file_size)}</span>
            </div>
          )}
        </div>

        {/* 기술적 세부사항 */}
        {showTechnicalDetails && (
          <div className="border-t border-gray-200 pt-4">
            <button
              onClick={() => toggleSection('technical')}
              className="flex items-center justify-between w-full text-left"
            >
              <h4 className="text-sm font-medium text-gray-700">기술적 세부사항</h4>
              <svg 
                className={`h-4 w-4 text-gray-500 transform transition-transform ${
                  expandedSections.has('technical') ? 'rotate-180' : ''
                }`}
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has('technical') && (
              <div className="mt-3 space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>예상 스트리밍 대역폭</span>
                  <span>{metadata.bitrate}kbps</span>
                </div>
                
                <div className="flex justify-between">
                  <span>오디오 품질 점수</span>
                  <span>
                    {metadata.bitrate >= 192 ? '9/10' :
                     metadata.bitrate >= 128 ? '7/10' :
                     metadata.bitrate >= 64 ? '6/10' : '4/10'}
                  </span>
                </div>
                
                <div className="flex justify-between">
                  <span>압축 효율성</span>
                  <span>
                    {metadata.format === 'aac' ? '높음' :
                     metadata.format === 'mp3' ? '중간' :
                     metadata.format === 'wav' ? '없음' : '알 수 없음'}
                  </span>
                </div>
                
                {metadata.file_size && metadata.duration > 0 && (
                  <div className="flex justify-between">
                    <span>실제 비트레이트</span>
                    <span>{calculateBitrate(metadata.file_size, metadata.duration)}kbps</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 원본과 비교 */}
        {showComparison && originalMetadata && (
          <div className="border-t border-gray-200 pt-4">
            <button
              onClick={() => toggleSection('comparison')}
              className="flex items-center justify-between w-full text-left"
            >
              <h4 className="text-sm font-medium text-gray-700">원본과 비교</h4>
              <svg 
                className={`h-4 w-4 text-gray-500 transform transition-transform ${
                  expandedSections.has('comparison') ? 'rotate-180' : ''
                }`}
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {expandedSections.has('comparison') && (
              <div className="mt-3">
                <MetadataComparison 
                  original={originalMetadata}
                  processed={metadata}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

interface MetadataComparisonProps {
  original: AudioMetadata
  processed: AudioMetadata
}

function MetadataComparison({ original, processed }: MetadataComparisonProps) {
  const calculateCompressionRatio = () => {
    if (original.file_size && processed.file_size) {
      return (original.file_size / processed.file_size).toFixed(2)
    }
    return null
  }

  const getBitrateChange = () => {
    const change = processed.bitrate - original.bitrate
    if (change > 0) return { text: `+${change}kbps`, color: 'text-red-600' }
    if (change < 0) return { text: `${change}kbps`, color: 'text-green-600' }
    return { text: '변화 없음', color: 'text-gray-600' }
  }

  const compressionRatio = calculateCompressionRatio()
  const bitrateChange = getBitrateChange()

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="grid grid-cols-3 gap-4 text-xs">
        <div className="text-center">
          <div className="text-gray-600 mb-1">원본</div>
          <div className="space-y-1">
            <div>{original.bitrate}kbps</div>
            <div>{getChannelText(original.channels)}</div>
            <div>{original.format.toUpperCase()}</div>
            {original.file_size && <div>{formatFileSize(original.file_size)}</div>}
          </div>
        </div>
        
        <div className="text-center border-x border-gray-200">
          <div className="text-gray-600 mb-1">변화</div>
          <div className="space-y-1">
            <div className={bitrateChange.color}>{bitrateChange.text}</div>
            <div className="text-gray-600">
              {original.channels !== processed.channels ? 
                `${getChannelText(original.channels)} → ${getChannelText(processed.channels)}` :
                '변화 없음'
              }
            </div>
            <div className="text-gray-600">
              {original.format !== processed.format ?
                `${original.format.toUpperCase()} → ${processed.format.toUpperCase()}` :
                '변화 없음'
              }
            </div>
            {compressionRatio && (
              <div className="text-green-600 font-medium">
                {compressionRatio}x 압축
              </div>
            )}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-gray-600 mb-1">처리 후</div>
          <div className="space-y-1">
            <div>{processed.bitrate}kbps</div>
            <div>{getChannelText(processed.channels)}</div>
            <div>{processed.format.toUpperCase()}</div>
            {processed.file_size && <div>{formatFileSize(processed.file_size)}</div>}
          </div>
        </div>
      </div>
    </div>
  )
}

interface RealTimeMetadataProps {
  chapterId: string
  className?: string
}

export function RealTimeMetadata({ chapterId, className = '' }: RealTimeMetadataProps) {
  const [metadata, setMetadata] = useState<AudioMetadata | null>(null)
  const [originalMetadata, setOriginalMetadata] = useState<AudioMetadata | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setLoading(true)
        setError(null)

        // 챕터 정보 조회
        const response = await fetch(`/api/v1/audio/${chapterId.split('/')[0]}/chapters/${chapterId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('voj_access_token')}`
          }
        })

        if (!response.ok) {
          throw new Error('Failed to fetch chapter metadata')
        }

        const chapterData = await response.json()
        
        if (chapterData.audio_metadata) {
          const meta: AudioMetadata = {
            duration: chapterData.audio_metadata.duration || 0,
            bitrate: chapterData.audio_metadata.bitrate || 0,
            sample_rate: chapterData.audio_metadata.sample_rate || 0,
            channels: chapterData.audio_metadata.channels || 0,
            format: chapterData.audio_metadata.format || 'unknown',
            file_size: chapterData.file_size || 0
          }
          
          setMetadata(meta)
          
          // 원본 메타데이터 설정 (처음 한 번만)
          if (!originalMetadata) {
            setOriginalMetadata(meta)
          }
        }
        
        setLastUpdated(new Date())

      } catch (err) {
        setError(err instanceof Error ? err.message : '메타데이터 조회 실패')
      } finally {
        setLoading(false)
      }
    }

    if (chapterId) {
      fetchMetadata()
      
      // 5초마다 자동 업데이트
      const interval = setInterval(fetchMetadata, 5000)
      return () => clearInterval(interval)
    }
  }, [chapterId, originalMetadata])

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="text-sm text-red-600">
          메타데이터를 불러올 수 없습니다: {error}
        </div>
      </div>
    )
  }

  if (!metadata) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="text-sm text-gray-600 text-center">
          메타데이터가 아직 추출되지 않았습니다.
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      <AudioMetadataDisplay
        metadata={metadata}
        showTechnicalDetails={true}
        showComparison={!!originalMetadata}
        originalMetadata={originalMetadata || undefined}
      />
      
      {lastUpdated && (
        <div className="mt-2 text-xs text-gray-500 text-center">
          마지막 업데이트: {lastUpdated.toLocaleTimeString('ko-KR')}
        </div>
      )}
    </div>
  )
}

interface MetadataProgressProps {
  progress: number
  currentStep: string
  estimatedMetadata?: Partial<AudioMetadata>
  className?: string
}

export function MetadataProgress({ 
  progress, 
  currentStep, 
  estimatedMetadata,
  className = '' 
}: MetadataProgressProps) {
  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center space-x-3 mb-3">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
        <span className="text-sm font-medium text-blue-800">메타데이터 추출 중...</span>
      </div>
      
      {/* 진행률 바 */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-blue-700 mb-1">
          <span>{currentStep}</span>
          <span>{Math.round(progress * 100)}%</span>
        </div>
        <div className="w-full bg-blue-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      </div>
      
      {/* 예상 메타데이터 */}
      {estimatedMetadata && (
        <div className="text-xs text-blue-700">
          <div className="font-medium mb-1">예상 정보:</div>
          <div className="space-y-1">
            {estimatedMetadata.duration && (
              <div>재생시간: ~{formatDuration(estimatedMetadata.duration)}</div>
            )}
            {estimatedMetadata.bitrate && (
              <div>비트레이트: ~{estimatedMetadata.bitrate}kbps</div>
            )}
            {estimatedMetadata.format && (
              <div>형식: {estimatedMetadata.format.toUpperCase()}</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// 유틸리티 함수들을 외부에서도 사용할 수 있도록 export
export function getChannelText(channels: number): string {
  switch (channels) {
    case 1: return '모노'
    case 2: return '스테레오'
    default: return `${channels}채널`
  }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export function calculateBitrate(fileSize: number, duration: number): number {
  if (duration === 0) return 0
  return Math.round((fileSize * 8) / (duration * 1000)) // kbps
}
