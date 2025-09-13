'use client'

import React, { useEffect, useState } from 'react'

interface UndoNotificationProps {
  isVisible: boolean
  message: string
  onUndo: () => void
  onDismiss: () => void
  timeLeft: number
}

export function UndoNotification({
  isVisible,
  message,
  onUndo,
  onDismiss,
  timeLeft
}: UndoNotificationProps) {
  const [progress, setProgress] = useState(100)

  useEffect(() => {
    if (isVisible && timeLeft > 0) {
      const interval = setInterval(() => {
        const newProgress = (timeLeft / 10000) * 100
        setProgress(newProgress)
      }, 100)

      return () => clearInterval(interval)
    }
  }, [isVisible, timeLeft])

  if (!isVisible) return null

  return (
    <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
      <div className="bg-gray-900 text-white rounded-lg shadow-lg p-4 max-w-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <svg className="h-5 w-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span className="text-sm">{message}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={onUndo}
              className="text-sm bg-white text-gray-900 px-3 py-1 rounded hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-white"
            >
              실행 취소
            </button>
            <button
              onClick={onDismiss}
              className="text-gray-400 hover:text-white focus:outline-none"
              aria-label="알림 닫기"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* 진행률 바 */}
        <div className="mt-2 bg-gray-700 rounded-full h-1">
          <div 
            className="bg-yellow-400 h-1 rounded-full transition-all duration-100 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <div className="mt-1 text-xs text-gray-400 text-center">
          {Math.ceil(timeLeft / 1000)}초 후 영구 삭제
        </div>
      </div>
    </div>
  )
}
