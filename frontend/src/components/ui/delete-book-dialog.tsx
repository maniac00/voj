'use client'

import React, { useState, useEffect } from 'react'
import { BookDto } from '@/lib/api'

interface DeleteBookDialogProps {
  book: BookDto | null
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
  loading?: boolean
}

export function DeleteBookDialog({
  book,
  isOpen,
  onClose,
  onConfirm,
  loading = false
}: DeleteBookDialogProps) {
  const [typedTitle, setTypedTitle] = useState('')
  const [acknowledgedWarnings, setAcknowledgedWarnings] = useState({
    dataLoss: false,
    audioFiles: false,
    irreversible: false
  })
  const [isConfirming, setIsConfirming] = useState(false)

  // 다이얼로그가 열릴 때마다 상태 초기화
  useEffect(() => {
    if (isOpen) {
      setTypedTitle('')
      setAcknowledgedWarnings({
        dataLoss: false,
        audioFiles: false,
        irreversible: false
      })
      setIsConfirming(false)
    }
  }, [isOpen])

  // ESC 키로 다이얼로그 닫기
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isConfirming) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, isConfirming, onClose])

  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isConfirming) {
      onClose()
    }
  }

  const handleConfirm = async () => {
    setIsConfirming(true)
    
    try {
      await onConfirm()
      onClose()
    } catch (error) {
      console.error('Delete failed:', error)
      // 에러가 발생해도 다이얼로그는 유지하여 사용자가 재시도할 수 있도록 함
    } finally {
      setIsConfirming(false)
    }
  }

  const isDeleteEnabled = 
    book &&
    typedTitle === book.title &&
    acknowledgedWarnings.dataLoss &&
    acknowledgedWarnings.audioFiles &&
    acknowledgedWarnings.irreversible

  if (!isOpen || !book) return null

  return (
    <div 
      className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4"
      onClick={handleBackgroundClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
      aria-describedby="delete-dialog-description"
    >
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center mb-4">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>
          </div>

          <h3 id="delete-dialog-title" className="text-lg font-medium text-gray-900 text-center mb-2">
            책 삭제 확인
          </h3>

          <div id="delete-dialog-description" className="text-sm text-gray-600 text-center mb-6">
            <strong>"{book.title}"</strong>을(를) 삭제하려고 합니다.
          </div>

          {/* 경고 체크리스트 */}
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
            <h4 className="text-sm font-medium text-red-800 mb-3">삭제 시 주의사항</h4>
            <div className="space-y-2">
              <label className="flex items-start space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={acknowledgedWarnings.dataLoss}
                  onChange={(e) => setAcknowledgedWarnings(prev => ({ 
                    ...prev, 
                    dataLoss: e.target.checked 
                  }))}
                  className="mt-0.5 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                  disabled={isConfirming}
                />
                <span className="text-red-700">
                  책의 모든 메타데이터(제목, 저자, 설명 등)가 영구적으로 삭제됩니다.
                </span>
              </label>
              
              <label className="flex items-start space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={acknowledgedWarnings.audioFiles}
                  onChange={(e) => setAcknowledgedWarnings(prev => ({ 
                    ...prev, 
                    audioFiles: e.target.checked 
                  }))}
                  className="mt-0.5 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                  disabled={isConfirming}
                />
                <span className="text-red-700">
                  연관된 모든 오디오 파일({book.total_chapters || 0}개 챕터)이 삭제됩니다.
                </span>
              </label>
              
              <label className="flex items-start space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={acknowledgedWarnings.irreversible}
                  onChange={(e) => setAcknowledgedWarnings(prev => ({ 
                    ...prev, 
                    irreversible: e.target.checked 
                  }))}
                  className="mt-0.5 h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                  disabled={isConfirming}
                />
                <span className="text-red-700">
                  이 작업은 되돌릴 수 없으며, 백업이나 복구가 불가능합니다.
                </span>
              </label>
            </div>
          </div>

          {/* 제목 입력 확인 */}
          <div className="mb-6">
            <label htmlFor="confirm-title" className="block text-sm font-medium text-gray-700 mb-2">
              계속하려면 책 제목을 정확히 입력하세요:
            </label>
            <div className="text-xs text-gray-500 mb-2">
              입력해야 할 제목: <strong>{book.title}</strong>
            </div>
            <input
              id="confirm-title"
              type="text"
              value={typedTitle}
              onChange={(e) => setTypedTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="책 제목을 입력하세요"
              autoComplete="off"
              disabled={isConfirming}
            />
            {typedTitle && typedTitle !== book.title && (
              <p className="mt-1 text-xs text-red-600">
                제목이 일치하지 않습니다.
              </p>
            )}
          </div>

          {/* 버튼 */}
          <div className="flex justify-center space-x-3">
            <button
              onClick={onClose}
              disabled={isConfirming}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              취소
            </button>
            <button
              onClick={handleConfirm}
              disabled={!isDeleteEnabled || isConfirming || loading}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isConfirming || loading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>삭제 중...</span>
                </div>
              ) : (
                '책 삭제'
              )}
            </button>
          </div>

          {/* 도움말 */}
          <div className="mt-4 text-xs text-gray-500 text-center">
            <p>실수로 삭제하는 것을 방지하기 위해 여러 단계의 확인이 필요합니다.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
