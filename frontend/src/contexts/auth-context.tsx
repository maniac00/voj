'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, getStoredToken, getStoredUser, clearAuthData, getCurrentUser } from '@/lib/auth/simple-auth'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  error: string | null
  logout: () => void
  refreshUser: () => Promise<void>
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const isAuthenticated = user !== null

  const logout = () => {
    clearAuthData()
    setUser(null)
    setError(null)
  }

  const clearError = () => {
    setError(null)
  }

  const refreshUser = async () => {
    const token = getStoredToken()
    
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const currentUser = await getCurrentUser()
      setUser(currentUser)
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh user'
      console.warn('Failed to refresh user:', errorMessage)
      setError(errorMessage)
      clearAuthData()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // 초기 로드 시 저장된 사용자 정보 확인
    const initAuth = async () => {
      const storedUser = getStoredUser()
      const token = getStoredToken()

      if (storedUser && token) {
        setUser(storedUser)
        // 백그라운드에서 사용자 정보 갱신
        try {
          const currentUser = await getCurrentUser()
          setUser(currentUser)
        } catch (error) {
          // 토큰이 만료되었거나 유효하지 않음
          console.warn('Token validation failed:', error)
          clearAuthData()
          setUser(null)
        }
      }
      
      setLoading(false)
    }

    initAuth()
  }, [])

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    error,
    logout,
    refreshUser,
    clearError,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
