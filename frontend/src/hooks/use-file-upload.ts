'use client'

import { useState, useCallback } from 'react'
import { getAuthHeaders } from '@/lib/auth/simple-auth'

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface UploadResult {
  success: boolean
  chapter_id?: string
  file_id?: string
  chapter_number?: number
  title?: string
  status?: string
  message?: string
  error?: string
}

export interface UploadOptions {
  onProgress?: (progress: UploadProgress) => void
  onSuccess?: (result: UploadResult) => void
  onError?: (error: string) => void
  signal?: AbortSignal
}

export function useFileUpload() {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({ loaded: 0, total: 0, percentage: 0 })

  const uploadAudioFile = useCallback(async (
    file: File,
    bookId: string,
    chapterTitle?: string,
    options: UploadOptions = {}
  ): Promise<UploadResult> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      const formData = new FormData()
      
      formData.append('file', file)
      
      // 챕터 제목 (파일명에서 확장자 제거)
      const title = chapterTitle || file.name.replace(/\.[^/.]+$/, "")
      
      setIsUploading(true)
      setUploadProgress({ loaded: 0, total: file.size, percentage: 0 })

      // 진행률 추적
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress: UploadProgress = {
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100)
          }
          
          setUploadProgress(progress)
          options.onProgress?.(progress)
        }
      })

      // 업로드 완료
      xhr.addEventListener('load', () => {
        setIsUploading(false)
        
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result: UploadResult = JSON.parse(xhr.responseText)
            options.onSuccess?.(result)
            resolve(result)
          } catch (error) {
            const errorMessage = 'Invalid response format'
            options.onError?.(errorMessage)
            reject(new Error(errorMessage))
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText)
            const errorMessage = errorData.detail || `Upload failed with status ${xhr.status}`
            options.onError?.(errorMessage)
            reject(new Error(errorMessage))
          } catch {
            const errorMessage = `Upload failed with status ${xhr.status}`
            options.onError?.(errorMessage)
            reject(new Error(errorMessage))
          }
        }
      })

      // 네트워크 에러
      xhr.addEventListener('error', () => {
        setIsUploading(false)
        const errorMessage = 'Network error occurred'
        options.onError?.(errorMessage)
        reject(new Error(errorMessage))
      })

      // 업로드 중단
      xhr.addEventListener('abort', () => {
        setIsUploading(false)
        const errorMessage = 'Upload was cancelled'
        options.onError?.(errorMessage)
        reject(new Error(errorMessage))
      })

      // 중단 신호 처리
      if (options.signal) {
        options.signal.addEventListener('abort', () => {
          xhr.abort()
        })
      }

      // 요청 설정
      const url = `/api/v1/files/upload/audio?book_id=${encodeURIComponent(bookId)}&chapter_title=${encodeURIComponent(title)}`
      xhr.open('POST', url)
      
      // 인증 헤더 추가
      const authHeaders = getAuthHeaders()
      Object.entries(authHeaders).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value)
      })
      
      // 업로드 시작
      xhr.send(formData)
    })
  }, [])

  const cancelUpload = useCallback(() => {
    // AbortController를 통해 업로드 중단 (구현 시)
    setIsUploading(false)
  }, [])

  return {
    uploadAudioFile,
    cancelUpload,
    isUploading,
    uploadProgress
  }
}

export interface BatchUploadItem {
  id: string
  file: File
  chapterTitle?: string
  progress: UploadProgress
  status: 'pending' | 'uploading' | 'completed' | 'error'
  result?: UploadResult
  error?: string
  abortController?: AbortController
}

export function useBatchFileUpload() {
  const [uploadItems, setUploadItems] = useState<BatchUploadItem[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const addFiles = useCallback((files: File[], bookId: string) => {
    const newItems: BatchUploadItem[] = files.map(file => ({
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      file,
      chapterTitle: file.name.replace(/\.[^/.]+$/, ""),
      progress: { loaded: 0, total: file.size, percentage: 0 },
      status: 'pending',
      abortController: new AbortController()
    }))

    setUploadItems(prev => [...prev, ...newItems])
    return newItems
  }, [])

  const uploadAll = useCallback(async (bookId: string) => {
    const pendingItems = uploadItems.filter(item => item.status === 'pending')
    
    if (pendingItems.length === 0) return

    setIsUploading(true)

    // 순차 업로드 (동시 업로드는 서버 부하 고려하여 제한)
    for (const item of pendingItems) {
      try {
        // 상태 업데이트
        setUploadItems(prev => 
          prev.map(i => i.id === item.id ? { ...i, status: 'uploading' } : i)
        )

        // 직접 업로드 로직 구현 (useFileUpload 훅 사용하지 않음)
        const result = await uploadSingleFile(
          item.file,
          bookId,
          item.chapterTitle,
          {
            onProgress: (progress) => {
              setUploadItems(prev => 
                prev.map(i => i.id === item.id ? { ...i, progress } : i)
              )
            },
            signal: item.abortController?.signal
          }
        )

        // 성공 처리
        setUploadItems(prev => 
          prev.map(i => i.id === item.id ? { 
            ...i, 
            status: 'completed',
            result 
          } : i)
        )

      } catch (error) {
        // 에러 처리
        setUploadItems(prev => 
          prev.map(i => i.id === item.id ? { 
            ...i, 
            status: 'error',
            error: error instanceof Error ? error.message : 'Upload failed'
          } : i)
        )
      }
    }

    setIsUploading(false)
  }, [uploadItems])

  // 단일 파일 업로드 함수
  const uploadSingleFile = async (
    file: File,
    bookId: string,
    chapterTitle?: string,
    options: UploadOptions = {}
  ): Promise<UploadResult> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      const formData = new FormData()
      
      formData.append('file', file)
      
      const title = chapterTitle || file.name.replace(/\.[^/.]+$/, "")

      // 진행률 추적
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress: UploadProgress = {
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100)
          }
          
          options.onProgress?.(progress)
        }
      })

      // 업로드 완료
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result: UploadResult = JSON.parse(xhr.responseText)
            resolve(result)
          } catch (error) {
            reject(new Error('Invalid response format'))
          }
        } else {
          try {
            const errorData = JSON.parse(xhr.responseText)
            reject(new Error(errorData.detail || `Upload failed with status ${xhr.status}`))
          } catch {
            reject(new Error(`Upload failed with status ${xhr.status}`))
          }
        }
      })

      // 네트워크 에러
      xhr.addEventListener('error', () => {
        reject(new Error('Network error occurred'))
      })

      // 업로드 중단
      xhr.addEventListener('abort', () => {
        reject(new Error('Upload was cancelled'))
      })

      // 중단 신호 처리
      if (options.signal) {
        options.signal.addEventListener('abort', () => {
          xhr.abort()
        })
      }

      // 요청 설정
      const url = `/api/v1/files/upload/audio?book_id=${encodeURIComponent(bookId)}&chapter_title=${encodeURIComponent(title)}`
      xhr.open('POST', url)
      
      // 인증 헤더 추가
      const authHeaders = getAuthHeaders()
      Object.entries(authHeaders).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value)
      })
      
      // 업로드 시작
      xhr.send(formData)
    })
  }

  const cancelUpload = useCallback((itemId: string) => {
    const item = uploadItems.find(i => i.id === itemId)
    if (item && item.abortController) {
      item.abortController.abort()
    }
    
    setUploadItems(prev => 
      prev.map(i => i.id === itemId ? { ...i, status: 'error', error: 'Cancelled by user' } : i)
    )
  }, [uploadItems])

  const removeItem = useCallback((itemId: string) => {
    setUploadItems(prev => prev.filter(item => item.id !== itemId))
  }, [])

  const retryItem = useCallback((itemId: string) => {
    setUploadItems(prev => 
      prev.map(i => i.id === itemId ? { 
        ...i, 
        status: 'pending',
        error: undefined,
        progress: { loaded: 0, total: i.file.size, percentage: 0 }
      } : i)
    )
  }, [])

  const clearCompleted = useCallback(() => {
    setUploadItems(prev => prev.filter(item => item.status !== 'completed'))
  }, [])

  return {
    uploadItems,
    isUploading,
    addFiles,
    uploadAll,
    cancelUpload,
    removeItem,
    retryItem,
    clearCompleted
  }
}
