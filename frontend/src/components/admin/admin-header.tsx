'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { logout as logoutApi } from '@/lib/auth/simple-auth'

export function AdminHeader() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await logoutApi()
      logout()
      router.push('/login')
    } catch (error) {
      console.warn('Logout failed:', error)
      // 로그아웃 API 실패해도 로컬 상태는 정리
      logout()
      router.push('/login')
    }
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* 로고 및 네비게이션 */}
          <div className="flex items-center space-x-8">
            <Link 
              href="/books" 
              className="text-xl font-semibold text-gray-900 hover:text-gray-700"
            >
              VOJ Admin
            </Link>
            
            <nav className="hidden md:flex space-x-6">
              <Link 
                href="/books" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                책 관리
              </Link>
              <Link 
                href="/dashboard" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                대시보드
              </Link>
            </nav>
          </div>

          {/* 사용자 정보 및 로그아웃 */}
          <div className="flex items-center space-x-4">
            {user && (
              <span className="text-sm text-gray-600">
                환영합니다, {user.username}님
              </span>
            )}
            
            <button
              onClick={handleLogout}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2"
            >
              로그아웃
            </button>
          </div>
        </div>
      </div>

      {/* 모바일 네비게이션 (간단하게) */}
      <div className="md:hidden border-t border-gray-200 bg-gray-50">
        <nav className="px-4 py-3 space-y-1">
          <Link 
            href="/books" 
            className="block text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
          >
            책 관리
          </Link>
          <Link 
            href="/dashboard" 
            className="block text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
          >
            대시보드
          </Link>
        </nav>
      </div>
    </header>
  )
}
