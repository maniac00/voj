export const metadata = {
  title: 'VOJ Admin',
  description: 'Audiobook Admin for Accessibility'
}

import '../app/globals.css'
import React from 'react'
import { AuthProvider } from '@/contexts/auth-context'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-slate-900 antialiased">
        <a href="#main" className="skip-link">본문으로 건너뛰기</a>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}


