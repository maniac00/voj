export const metadata = {
  title: 'VOJ Admin',
  description: 'Audiobook Admin for Accessibility'
}

import '../app/globals.css'
import React from 'react'
import { AuthProvider } from '@/contexts/auth-context'
import { NotificationProvider } from '@/contexts/notification-context'

// 환경변수 디버깅 (클라이언트에서 확인 가능)
if (typeof window !== 'undefined') {
  console.group('🔍 VOJ Environment Check')
  console.log('API_URL:', process.env.NEXT_PUBLIC_API_URL || 'NOT SET')
  console.log('API_BASE:', process.env.NEXT_PUBLIC_API_BASE || 'NOT SET')
  console.log('Current Origin:', window.location.origin)
  console.groupEnd()
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        <div className="skip-links">
          <a href="#main" className="skip-link">본문으로 건너뛰기</a>
          <a href="#navigation" className="skip-link">내비게이션으로 건너뛰기</a>
          <a href="#search" className="skip-link">검색으로 건너뛰기</a>
        </div>
        <AuthProvider>
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </AuthProvider>
      </body>
    </html>
  )
}


