'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { login, storeToken, storeUser, getCurrentUser } from '@/lib/auth/simple-auth'
import { useAuth } from '@/contexts/auth-context'

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="flex min-h-screen items-center justify-center p-6">로딩 중...</main>}>
      <LoginForm />
    </Suspense>
  )
}

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { isAuthenticated, refreshUser } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 이미 로그인된 경우 리디렉션
  useEffect(() => {
    if (isAuthenticated) {
      const returnUrl = searchParams.get('returnUrl')
      const redirectTo = returnUrl ? decodeURIComponent(returnUrl) : '/books'
      router.push(redirectTo)
    }
  }, [isAuthenticated, router, searchParams])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // 로그인 API 호출
      const response = await login({ username, password })
      
      // 토큰 저장
      storeToken(response.access_token)
      
      // 사용자 정보 조회 및 저장
      const user = await getCurrentUser()
      storeUser(user)
      
      // Auth Context 갱신
      await refreshUser()
      
      // returnUrl이 있으면 해당 페이지로, 없으면 기본 페이지로 리디렉션
      const returnUrl = searchParams.get('returnUrl')
      const redirectTo = returnUrl ? decodeURIComponent(returnUrl) : '/books'
      router.push(redirectTo)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '로그인에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-semibold">관리자 로그인</h1>
          <p className="mt-2 text-sm text-gray-600">
            VOJ Audiobooks 관리자 시스템
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label 
              htmlFor="username" 
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              사용자명
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              placeholder="admin"
              autoComplete="username"
            />
          </div>
          
          <div>
            <label 
              htmlFor="password" 
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              비밀번호
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
              placeholder="비밀번호를 입력하세요"
              autoComplete="current-password"
            />
          </div>
          
          {error && (
            <div 
              className="text-red-600 text-sm bg-red-50 p-3 rounded-md"
              role="alert"
              aria-live="polite"
            >
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white py-2 px-4 rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>
        
        <div className="text-center text-xs text-gray-500">
          기본 계정: admin / admin123
        </div>
      </div>
    </main>
  )
}
