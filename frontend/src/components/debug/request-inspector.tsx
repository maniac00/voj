'use client'

import { useEffect, useState } from 'react'

/**
 * 실제 API 요청 URL 확인용 디버깅 컴포넌트
 */
export function RequestInspector() {
  const [testResult, setTestResult] = useState<string>('')

  useEffect(() => {
    async function testRequest() {
      try {
        console.group('🔬 Request Inspector')
        console.log('Testing /api/v1/health request...')

        const response = await fetch('/api/v1/health', {
          method: 'GET',
          cache: 'no-store',
        })

        console.log('Response URL:', response.url)
        console.log('Response Status:', response.status)
        console.log('Response Type:', response.type)

        const data = await response.json()
        console.log('Response Data:', data)
        console.groupEnd()

        setTestResult(`✅ Request successful: ${response.url} (${response.status})`)
      } catch (error) {
        console.error('Request failed:', error)
        console.groupEnd()
        setTestResult(`❌ Request failed: ${error}`)
      }
    }

    testRequest()
  }, [])

  if (!testResult) return null

  return (
    <div style={{
      position: 'fixed',
      bottom: 10,
      right: 10,
      background: '#000',
      color: '#0f0',
      padding: '10px',
      fontSize: '12px',
      zIndex: 9999,
      maxWidth: '400px',
      fontFamily: 'monospace'
    }}>
      {testResult}
    </div>
  )
}
