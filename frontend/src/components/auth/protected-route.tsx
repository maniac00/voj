'use client'

import React, { ReactNode, useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'

interface ProtectedRouteProps {
  children: ReactNode
  fallback?: ReactNode
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    // 로딩이 완료되고 인증되지 않은 경우 로그인 페이지로 리디렉션
    if (!loading && !isAuthenticated) {
      // 현재 경로를 저장하여 로그인 후 돌아올 수 있도록 함
      const returnUrl = encodeURIComponent(pathname)
      
      // 부드러운 리디렉션을 위해 약간의 지연
      setTimeout(() => {
        router.push(`/login?returnUrl=${returnUrl}`)
      }, 100)
    }
  }, [isAuthenticated, loading, router, pathname])

  // 로딩 중일 때 표시할 컴포넌트
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto"></div>
          <p className="text-gray-600">로딩 중...</p>
        </div>
      </div>
    )
  }

  // 인증되지 않은 경우 fallback 컴포넌트 표시 (옵션)
  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>
    }
    
    // 기본 fallback: 빈 화면 (리디렉션이 진행 중)
    return null
  }

  // 인증된 경우 자식 컴포넌트 렌더링
  return <>{children}</>
}

/**
 * 관리자 권한이 필요한 페이지를 보호하는 HOC
 */
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  const AuthenticatedComponent = (props: P) => {
    return (
      <ProtectedRoute fallback={fallback}>
        <WrappedComponent {...props} />
      </ProtectedRoute>
    )
  }

  AuthenticatedComponent.displayName = `withAuth(${WrappedComponent.displayName || WrappedComponent.name})`

  return AuthenticatedComponent
}
