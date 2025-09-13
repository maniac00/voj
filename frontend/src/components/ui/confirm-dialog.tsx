'use client'

import React, { useState, useEffect } from 'react'

interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void | Promise<void>
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  destructive?: boolean
  requireTyping?: string
  loading?: boolean
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = '확인',
  cancelText = '취소',
  destructive = false,
  requireTyping,
  loading = false
}: ConfirmDialogProps) {
  const [typedText, setTypedText] = useState('')
  const [isConfirming, setIsConfirming] = useState(false)

  // 다이얼로그가 열릴 때마다 입력 텍스트 초기화
  useEffect(() => {
    if (isOpen) {
      setTypedText('')
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

  // 배경 클릭으로 다이얼로그 닫기
  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isConfirming) {
      onClose()
    }
  }

  const handleConfirm = async () => {
    if (requireTyping && typedText !== requireTyping) {
      return
    }

    setIsConfirming(true)
    
    try {
      await onConfirm()
      onClose()
    } catch (error) {
      console.error('Confirm action failed:', error)
      // 에러가 발생해도 다이얼로그는 유지하여 사용자가 재시도할 수 있도록 함
    } finally {
      setIsConfirming(false)
    }
  }

  const isConfirmEnabled = !requireTyping || typedText === requireTyping

  if (!isOpen) return null

  return (
    <div 
      className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4"
      onClick={handleBackgroundClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          {/* 아이콘 */}
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            {destructive ? (
              <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            ) : (
              <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>

          {/* 제목 */}
          <h3 id="dialog-title" className="text-lg font-medium text-gray-900 text-center mb-2">
            {title}
          </h3>

          {/* 메시지 */}
          <div id="dialog-description" className="text-sm text-gray-500 text-center mb-4">
            <div dangerouslySetInnerHTML={{ __html: message }} />
          </div>

          {/* 타이핑 확인 */}
          {requireTyping && (
            <div className="mb-4">
              <label htmlFor="confirm-typing" className="block text-sm font-medium text-gray-700 mb-2">
                계속하려면 <strong>"{requireTyping}"</strong>을(를) 입력하세요:
              </label>
              <input
                id="confirm-typing"
                type="text"
                value={typedText}
                onChange={(e) => setTypedText(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder={requireTyping}
                autoComplete="off"
                disabled={isConfirming}
              />
            </div>
          )}

          {/* 버튼 */}
          <div className="flex justify-center space-x-3">
            <button
              onClick={onClose}
              disabled={isConfirming}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelText}
            </button>
            <button
              onClick={handleConfirm}
              disabled={!isConfirmEnabled || isConfirming || loading}
              className={`px-4 py-2 text-sm font-medium text-white border border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                destructive
                  ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                  : 'bg-black hover:bg-gray-800 focus:ring-black'
              }`}
            >
              {isConfirming || loading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>처리 중...</span>
                </div>
              ) : (
                confirmText
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
