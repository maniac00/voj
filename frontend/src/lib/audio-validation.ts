/**
 * 오디오 파일 유효성 검증 유틸리티
 * MP3, WAV, M4A, FLAC 파일의 상세 검증
 */

export interface AudioValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
  fileInfo?: {
    duration?: number
    bitrate?: number
    sampleRate?: number
    channels?: number
    format?: string
  }
}

export interface AudioValidationOptions {
  maxFileSize?: number // 바이트 단위
  minDuration?: number // 초 단위
  maxDuration?: number // 초 단위
  allowedFormats?: string[]
  minBitrate?: number // kbps
  maxBitrate?: number // kbps
  allowedSampleRates?: number[]
  requireMono?: boolean
}

const DEFAULT_OPTIONS: AudioValidationOptions = {
  maxFileSize: 100 * 1024 * 1024, // 100MB
  minDuration: 10, // 10초 이상
  maxDuration: 4 * 60 * 60, // 4시간 이하
  // MVP: mp4 컨테이너만 허용 (m4a 포함)
  allowedFormats: ['.mp4', '.m4a'],
  minBitrate: 32, // 32kbps 이상
  maxBitrate: 320, // 320kbps 이하
  allowedSampleRates: [8000, 11025, 16000, 22050, 44100, 48000],
  requireMono: false
}

/**
 * 파일 확장자 검증
 */
function validateFileExtension(fileName: string, allowedFormats: string[]): string | null {
  const extension = '.' + fileName.split('.').pop()?.toLowerCase()
  
  if (!allowedFormats.includes(extension)) {
    return `지원되지 않는 파일 형식입니다. 지원 형식: ${allowedFormats.join(', ')}`
  }
  
  return null
}

/**
 * 파일 크기 검증
 */
function validateFileSize(file: File, maxSize: number): string | null {
  if (file.size > maxSize) {
    const maxSizeMB = Math.round(maxSize / (1024 * 1024))
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
    return `파일 크기가 너무 큽니다. 현재: ${fileSizeMB}MB, 최대: ${maxSizeMB}MB`
  }
  
  if (file.size < 1024) {
    return '파일이 너무 작습니다. 유효한 오디오 파일인지 확인해주세요.'
  }
  
  return null
}

/**
 * 파일명 검증
 */
function validateFileName(fileName: string): string[] {
  const issues: string[] = []
  
  // 금지 문자만 차단 (Windows/FileSystem 위험 문자)
  if (/[<>:"/\\|?*]/.test(fileName)) {
    issues.push('파일명에 사용할 수 없는 문자가 포함되어 있습니다. (< > : " / \\ | ? *)')
  }
  
  // 경로 순회 방지
  if (fileName.includes('..')) {
    issues.push('파일명에 .. 을 포함할 수 없습니다.')
  }
  
  // 길이 검증 (UTF-16 기준 문자열 길이 체크)
  if (fileName.length > 255) {
    issues.push('파일명이 너무 깁니다. (최대 255자)')
  }
  
  // 앞뒤 공백 경고 (에러 아님)
  if (fileName.trim() !== fileName) {
    issues.push('파일명 앞뒤 공백이 제거됩니다.')
  }
  
  return issues
}

/**
 * MIME 타입 검증
 */
function validateMimeType(file: File): string | null {
  const allowedMimeTypes = [
    'audio/mp4',      // M4A/MP4 (오디오)
    'audio/x-m4a'     // 일부 브라우저에서 보고
  ]
  
  if (!allowedMimeTypes.includes(file.type)) {
    return `지원되지 않는 MIME 타입입니다: ${file.type}`
  }
  
  return null
}

/**
 * 파일 헤더 검증 (매직 넘버)
 */
async function validateFileHeader(file: File): Promise<string | null> {
  try {
    const buffer = await file.slice(0, 12).arrayBuffer()
    const bytes = new Uint8Array(buffer)
    
    // ID3 태그로 시작하는 MP3는 유효로 간주 (프레임은 태그 뒤에 위치)
    if (bytes[0] === 0x49 && bytes[1] === 0x44 && bytes[2] === 0x33) { // 'ID3'
      return null
    }
    
    // M4A/MP4 검증 (ftyp 확인)
    if (bytes[4] === 0x66 && bytes[5] === 0x74 && bytes[6] === 0x79 && bytes[7] === 0x70) {
      return null // 유효한 M4A
    }
    
    return '파일 헤더가 올바르지 않습니다. 손상된 파일이거나 지원되지 않는 형식일 수 있습니다.'
    
  } catch (error) {
    return '파일 헤더를 읽을 수 없습니다.'
  }
}

/**
 * 클라이언트 사이드 오디오 메타데이터 추출 (Web Audio API)
 */
async function extractClientAudioMetadata(file: File): Promise<{
  duration?: number
  sampleRate?: number
  channels?: number
} | null> {
  try {
    // Web Audio API를 사용한 기본 메타데이터 추출
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const arrayBuffer = await file.arrayBuffer()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)
    
    const metadata = {
      duration: audioBuffer.duration,
      sampleRate: audioBuffer.sampleRate,
      channels: audioBuffer.numberOfChannels
    }
    
    audioContext.close()
    return metadata
    
  } catch (error) {
    console.warn('Client-side metadata extraction failed:', error)
    return null
  }
}

/**
 * 종합적인 오디오 파일 검증
 */
export async function validateAudioFile(
  file: File, 
  options: AudioValidationOptions = {}
): Promise<AudioValidationResult> {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  const errors: string[] = []
  const warnings: string[] = []
  
  // 1. 기본 파일 검증
  const extensionError = validateFileExtension(file.name, opts.allowedFormats || [])
  if (extensionError) {
    errors.push(extensionError)
  }
  
  const sizeError = validateFileSize(file, opts.maxFileSize || 0)
  if (sizeError) {
    errors.push(sizeError)
  }
  
  const mimeError = validateMimeType(file)
  if (mimeError) {
    errors.push(mimeError)
  }
  
  const fileNameIssues = validateFileName(file.name)
  fileNameIssues.forEach(issue => {
    if (issue.includes('오류') || issue.includes('특수문자') || issue.includes('길이')) {
      errors.push(issue)
    } else {
      warnings.push(issue)
    }
  })
  
  // 2. 파일 헤더 검증
  try {
    const headerError = await validateFileHeader(file)
    if (headerError) {
      errors.push(headerError)
    }
  } catch (error) {
    warnings.push('파일 헤더 검증을 건너뜁니다.')
  }
  
  // 기본 검증에서 오류가 있으면 여기서 중단
  if (errors.length > 0) {
    return {
      isValid: false,
      errors,
      warnings
    }
  }
  
  // 3. 오디오 메타데이터 검증 (선택적)
  let fileInfo: AudioValidationResult['fileInfo']
  
  try {
    // MP4는 Web Audio decode 실패가 잦을 수 있어 실패 시에도 통과
    const metadata = await extractClientAudioMetadata(file)
    if (metadata) {
      fileInfo = {
        duration: metadata.duration,
        sampleRate: metadata.sampleRate,
        channels: metadata.channels
      }
      
      // 재생시간 검증
      if (opts.minDuration && metadata.duration < opts.minDuration) {
        errors.push(`재생시간이 너무 짧습니다. 최소: ${opts.minDuration}초, 현재: ${Math.round(metadata.duration)}초`)
      }
      
      if (opts.maxDuration && metadata.duration > opts.maxDuration) {
        errors.push(`재생시간이 너무 깁니다. 최대: ${Math.round(opts.maxDuration / 60)}분, 현재: ${Math.round(metadata.duration / 60)}분`)
      }
      
      // 샘플레이트 검증
      if (opts.allowedSampleRates && !opts.allowedSampleRates.includes(metadata.sampleRate)) {
        warnings.push(`비표준 샘플레이트입니다: ${metadata.sampleRate}Hz`)
      }
      
      // 채널 검증
      if (opts.requireMono && metadata.channels > 1) {
        warnings.push('스테레오 파일입니다. 모노로 변환됩니다.')
      }
      
      // 품질 경고
      if (metadata.duration > 60 * 60) { // 1시간 이상
        warnings.push('긴 오디오 파일입니다. 업로드에 시간이 오래 걸릴 수 있습니다.')
      }
    }
  } catch (error) {
    warnings.push('메타데이터를 추출할 수 없습니다. 서버에서 다시 시도됩니다.')
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    fileInfo
  }
}

/**
 * 다중 파일 검증
 */
export async function validateAudioFiles(
  files: File[], 
  options: AudioValidationOptions = {}
): Promise<{
  validFiles: File[]
  invalidFiles: Array<{ file: File; result: AudioValidationResult }>
  totalDuration?: number
  totalSize: number
}> {
  const validFiles: File[] = []
  const invalidFiles: Array<{ file: File; result: AudioValidationResult }> = []
  let totalDuration = 0
  let totalSize = 0
  
  for (const file of files) {
    const result = await validateAudioFile(file, options)
    
    if (result.isValid) {
      validFiles.push(file)
      totalSize += file.size
      
      if (result.fileInfo?.duration) {
        totalDuration += result.fileInfo.duration
      }
    } else {
      invalidFiles.push({ file, result })
    }
  }
  
  return {
    validFiles,
    invalidFiles,
    totalDuration: totalDuration > 0 ? totalDuration : undefined,
    totalSize
  }
}

/**
 * 오디오북 챕터 파일명 분석
 */
export function analyzeChapterFileName(fileName: string): {
  suggestedTitle: string
  chapterNumber?: number
  bookTitle?: string
} {
  // 확장자 제거
  const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '')
  
  // 챕터 번호 패턴 찾기
  const chapterPatterns = [
    /(\d+)_(\d+)/, // "1_1" 형식
    /chapter\s*(\d+)/i, // "Chapter 1" 형식
    /(\d+)장/, // "1장" 형식
    /(\d+)편/, // "1편" 형식
    /(\d+)회/, // "1회" 형식
  ]
  
  let chapterNumber: number | undefined
  let suggestedTitle = nameWithoutExt
  
  for (const pattern of chapterPatterns) {
    const match = nameWithoutExt.match(pattern)
    if (match) {
      chapterNumber = parseInt(match[1])
      // 챕터 번호 부분을 제거하여 제목 추출
      suggestedTitle = nameWithoutExt.replace(pattern, '').trim()
      break
    }
  }
  
  // 책 제목과 챕터 제목 분리 시도
  let bookTitle: string | undefined
  
  if (suggestedTitle.includes(' - ')) {
    const parts = suggestedTitle.split(' - ')
    if (parts.length >= 2) {
      bookTitle = parts[0].trim()
      suggestedTitle = parts.slice(1).join(' - ').trim()
    }
  }
  
  // 빈 제목인 경우 기본값 설정
  if (!suggestedTitle) {
    suggestedTitle = chapterNumber ? `Chapter ${chapterNumber}` : '제목 없음'
  }
  
  return {
    suggestedTitle,
    chapterNumber,
    bookTitle
  }
}

/**
 * 파일 중복 검사
 */
export function checkDuplicateFiles(files: File[]): {
  duplicates: Array<{ original: File; duplicate: File }>
  uniqueFiles: File[]
} {
  const duplicates: Array<{ original: File; duplicate: File }> = []
  const uniqueFiles: File[] = []
  const seenFiles = new Map<string, File>()
  
  for (const file of files) {
    const key = `${file.name}-${file.size}-${file.lastModified}`
    
    if (seenFiles.has(key)) {
      duplicates.push({
        original: seenFiles.get(key)!,
        duplicate: file
      })
    } else {
      seenFiles.set(key, file)
      uniqueFiles.push(file)
    }
  }
  
  return { duplicates, uniqueFiles }
}

/**
 * 오디오북 시리즈 파일 분석
 */
export function analyzeAudiobookSeries(files: File[]): {
  suggestedBookTitle?: string
  chapters: Array<{
    file: File
    suggestedTitle: string
    chapterNumber?: number
  }>
  warnings: string[]
} {
  const warnings: string[] = []
  const chapters = files.map(file => analyzeChapterFileName(file.name))
  
  // 공통 책 제목 찾기
  const bookTitles = chapters.map(c => c.bookTitle).filter(Boolean)
  const suggestedBookTitle = bookTitles.length > 0 
    ? bookTitles.reduce((a, b) => a === b ? a : undefined)
    : undefined
  
  // 챕터 번호 연속성 확인
  const numberedChapters = chapters.filter(c => c.chapterNumber).sort((a, b) => (a.chapterNumber || 0) - (b.chapterNumber || 0))
  
  if (numberedChapters.length > 1) {
    for (let i = 1; i < numberedChapters.length; i++) {
      const prev = numberedChapters[i - 1].chapterNumber || 0
      const curr = numberedChapters[i].chapterNumber || 0
      
      if (curr - prev > 1) {
        warnings.push(`챕터 번호가 연속되지 않습니다: ${prev} → ${curr}`)
      }
    }
  }
  
  // 중복 챕터 번호 확인
  const chapterNumbers = chapters.map(c => c.chapterNumber).filter(Boolean)
  const duplicateNumbers = chapterNumbers.filter((num, index) => chapterNumbers.indexOf(num) !== index)
  
  if (duplicateNumbers.length > 0) {
    warnings.push(`중복된 챕터 번호가 있습니다: ${duplicateNumbers.join(', ')}`)
  }
  
  return {
    suggestedBookTitle,
    chapters: files.map((file, index) => ({
      file,
      suggestedTitle: chapters[index].suggestedTitle,
      chapterNumber: chapters[index].chapterNumber
    })),
    warnings
  }
}

/**
 * 빠른 기본 검증 (파일 선택 시 즉시 실행)
 */
export function quickValidateAudioFile(file: File): { isValid: boolean; error?: string } {
  // 파일 크기
  if (file.size > 100 * 1024 * 1024) {
    return { isValid: false, error: '파일 크기가 100MB를 초과합니다.' }
  }
  
  if (file.size < 1024) {
    return { isValid: false, error: '파일이 너무 작습니다.' }
  }
  
  // 파일 형식
  const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/flac']
  if (!allowedTypes.includes(file.type)) {
    return { isValid: false, error: '지원되지 않는 파일 형식입니다.' }
  }
  
  // 파일명(금지 문자만 차단)
  if (/[<>:"/\\|?*]/.test(file.name) || file.name.includes('..')) {
    return { isValid: false, error: '파일명에 사용할 수 없는 문자가 포함되어 있습니다.' }
  }
  
  return { isValid: true }
}
