/**
 * 간단한 세션 기반 인증 유틸리티
 * PRD v2.0 요구사항에 따른 하드코딩 인증 (admin/admin123)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface LoginCredentials {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  username: string
}

export interface User {
  sub: string
  username: string
  scope: string
}

// 토큰 저장 키
const TOKEN_KEY = 'voj_access_token'
const USER_KEY = 'voj_user_info'

/**
 * 로그인 API 호출
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(error.detail || 'Login failed')
  }

  return response.json()
}

/**
 * 로그아웃 API 호출
 */
export async function logout(): Promise<void> {
  const token = getStoredToken()
  
  if (token) {
    try {
      await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
    } catch (error) {
      console.warn('Logout API call failed:', error)
    }
  }
  
  // 로컬 스토리지 정리
  clearAuthData()
}

/**
 * 현재 사용자 정보 조회
 */
export async function getCurrentUser(): Promise<User> {
  const token = getStoredToken()
  
  if (!token) {
    throw new Error('No access token')
  }

  const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    clearAuthData()
    throw new Error('Failed to get user info')
  }

  return response.json()
}

/**
 * 토큰 저장 (localStorage + 쿠키)
 */
export function storeToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token)
    
    // 쿠키에도 저장하여 서버 사이드에서 접근 가능하도록 함
    // httpOnly는 false로 설정하여 클라이언트에서도 접근 가능
    document.cookie = `voj_access_token=${token}; path=/; max-age=86400; SameSite=Strict`
  }
}

/**
 * 저장된 토큰 조회
 */
export function getStoredToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(TOKEN_KEY)
  }
  return null
}

/**
 * 사용자 정보 저장
 */
export function storeUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

/**
 * 저장된 사용자 정보 조회
 */
export function getStoredUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem(USER_KEY)
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch {
        return null
      }
    }
  }
  return null
}

/**
 * 인증 데이터 정리 (localStorage + 쿠키)
 */
export function clearAuthData(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    
    // 쿠키도 삭제
    document.cookie = 'voj_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
  }
}

/**
 * 로그인 상태 확인
 */
export function isLoggedIn(): boolean {
  return getStoredToken() !== null
}

/**
 * API 요청에 인증 헤더 추가
 */
export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken()
  
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
    }
  }
  
  return {}
}
