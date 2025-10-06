export const metadata = {
  title: 'VOJ Admin',
  description: 'Audiobook Admin for Accessibility'
}

import '../app/globals.css'
import React from 'react'
import { AuthProvider } from '@/contexts/auth-context'
import { NotificationProvider } from '@/contexts/notification-context'
import { EnvChecker } from '@/components/debug/env-checker'
import { RequestInspector } from '@/components/debug/request-inspector'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        <EnvChecker />
        <RequestInspector />
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


