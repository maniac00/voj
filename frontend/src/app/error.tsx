'use client'

import { useEffect } from 'react'
import Link from 'next/link'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // 에러를 로깅 서비스에 전송할 수 있습니다
    console.error('Application error:', error)
  }, [error])

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-6 max-w-md">
        <div className="space-y-2">
          <div className="text-6xl">😵</div>
          <h1 className="text-2xl font-semibold text-gray-900">문제가 발생했습니다</h1>
          <p className="text-gray-600">
            예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.
          </p>
        </div>
        
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 text-left">
            <h3 className="font-medium text-red-800 mb-2">개발 모드 에러 정보:</h3>
            <pre className="text-xs text-red-700 overflow-auto">
              {error.message}
            </pre>
          </div>
        )}
        
        <div className="space-x-4">
          <button
            onClick={reset}
            className="inline-block bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
          >
            다시 시도
          </button>
          
          <Link 
            href="/"
            className="inline-block bg-gray-100 text-gray-700 px-6 py-3 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            홈으로 돌아가기
          </Link>
        </div>
        
        <div className="text-sm text-gray-500">
          문제가 지속되면 페이지를 새로고침하거나 관리자에게 문의해주세요.
        </div>
      </div>
    </div>
  )
}
