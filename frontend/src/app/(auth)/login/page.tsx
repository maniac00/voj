'use client'

import React from 'react'
import { signInWithRedirect } from 'aws-amplify/auth'

export default function LoginPage() {
  async function handleLogin() {
    await signInWithRedirect({ provider: 'COGNITO' })
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-semibold">로그인</h1>
        <button onClick={handleLogin} className="rounded bg-black px-4 py-2 text-white">
          Cognito로 로그인
        </button>
      </div>
    </main>
  )
}


