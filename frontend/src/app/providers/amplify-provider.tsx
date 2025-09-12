'use client'

import React, { useEffect, useRef } from 'react'
import { Amplify } from 'aws-amplify'
import { getAmplifyConfig } from '@/lib/auth/amplify-config'

export function AmplifyProvider({ children }: { children: React.ReactNode }) {
  const configuredRef = useRef(false)

  useEffect(() => {
    if (!configuredRef.current) {
      Amplify.configure(getAmplifyConfig())
      configuredRef.current = true
    }
  }, [])

  return <>{children}</>
}


