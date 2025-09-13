/**
 * 간단한 인증 유틸리티 테스트
 */
import {
  login,
  logout,
  getCurrentUser,
  storeToken,
  getStoredToken,
  storeUser,
  getStoredUser,
  clearAuthData,
  isLoggedIn,
  getAuthHeaders
} from './simple-auth'

// Mock fetch globally
const mockFetch = jest.fn()
global.fetch = mockFetch

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}

// Mock document.cookie
const mockDocument = {
  cookie: '',
}

// Setup mocks
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

Object.defineProperty(global, 'document', {
  value: mockDocument
})

describe('Simple Auth Utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockDocument.cookie = ''
    mockLocalStorage.getItem.mockReturnValue(null)
  })

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const mockResponse = {
        access_token: 'test-token',
        token_type: 'bearer',
        expires_in: 3600,
        username: 'admin'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      })

      const result = await login({ username: 'admin', password: 'admin123' })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username: 'admin', password: 'admin123' })
        }
      )

      expect(result).toEqual(mockResponse)
    })

    it('should throw error on failed login', async () => {
      const mockErrorResponse = {
        detail: 'Invalid username or password'
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve(mockErrorResponse)
      })

      await expect(login({ username: 'admin', password: 'wrong' }))
        .rejects.toThrow('Invalid username or password')
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(login({ username: 'admin', password: 'admin123' }))
        .rejects.toThrow('Network error')
    })
  })

  describe('logout', () => {
    it('should call logout API and clear auth data', async () => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Logged out successfully' })
      })

      await logout()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/logout',
        {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer test-token',
          },
        }
      )

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_access_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_user_info')
    })

    it('should clear auth data even if API call fails', async () => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await logout()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_access_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_user_info')
    })
  })

  describe('getCurrentUser', () => {
    it('should return user info with valid token', async () => {
      const mockUser = {
        sub: 'user-id',
        username: 'admin',
        scope: 'admin'
      }

      mockLocalStorage.getItem.mockReturnValue('test-token')
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser)
      })

      const result = await getCurrentUser()

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/me',
        {
          headers: {
            'Authorization': 'Bearer test-token',
          },
        }
      )

      expect(result).toEqual(mockUser)
    })

    it('should throw error when no token', async () => {
      mockLocalStorage.getItem.mockReturnValue(null)

      await expect(getCurrentUser()).rejects.toThrow('No access token')
    })

    it('should clear auth data on failed API call', async () => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401
      })

      await expect(getCurrentUser()).rejects.toThrow('Failed to get user info')

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_access_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_user_info')
    })
  })

  describe('token management', () => {
    it('should store and retrieve token', () => {
      // Mock window object for this test
      Object.defineProperty(window, 'document', {
        value: mockDocument,
        writable: true
      })

      storeToken('test-token')

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('voj_access_token', 'test-token')
      expect(mockDocument.cookie).toContain('voj_access_token=test-token')

      mockLocalStorage.getItem.mockReturnValue('test-token')
      const token = getStoredToken()

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('voj_access_token')
      expect(token).toBe('test-token')
    })

    it('should return null when no token stored', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      const token = getStoredToken()

      expect(token).toBeNull()
    })
  })

  describe('user management', () => {
    it('should store and retrieve user info', () => {
      const user = { sub: 'user-id', username: 'admin', scope: 'admin' }

      storeUser(user)

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'voj_user_info',
        JSON.stringify(user)
      )

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(user))
      const retrievedUser = getStoredUser()

      expect(retrievedUser).toEqual(user)
    })

    it('should return null when no user stored', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      const user = getStoredUser()

      expect(user).toBeNull()
    })

    it('should return null when stored user data is invalid JSON', () => {
      mockLocalStorage.getItem.mockReturnValue('invalid-json')
      const user = getStoredUser()

      expect(user).toBeNull()
    })
  })

  describe('clearAuthData', () => {
    it('should clear all auth data', () => {
      Object.defineProperty(window, 'document', {
        value: mockDocument,
        writable: true
      })

      clearAuthData()

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_access_token')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_user_info')
      expect(mockDocument.cookie).toContain('voj_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT')
    })
  })

  describe('isLoggedIn', () => {
    it('should return true when token exists', () => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
      
      expect(isLoggedIn()).toBe(true)
    })

    it('should return false when no token', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      
      expect(isLoggedIn()).toBe(false)
    })
  })

  describe('getAuthHeaders', () => {
    it('should return auth headers when token exists', () => {
      mockLocalStorage.getItem.mockReturnValue('test-token')
      
      const headers = getAuthHeaders()
      
      expect(headers).toEqual({
        'Authorization': 'Bearer test-token'
      })
    })

    it('should return empty headers when no token', () => {
      mockLocalStorage.getItem.mockReturnValue(null)
      
      const headers = getAuthHeaders()
      
      expect(headers).toEqual({})
    })
  })

  describe('server-side rendering', () => {
    it('should handle absence of window object', () => {
      // Mock window as undefined (SSR environment)
      const originalWindow = global.window
      // @ts-ignore
      delete global.window

      expect(() => {
        storeToken('test-token')
        getStoredToken()
        storeUser({ sub: 'test', username: 'test', scope: 'admin' })
        getStoredUser()
        clearAuthData()
      }).not.toThrow()

      // Restore window
      global.window = originalWindow
    })
  })
})

describe('Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockDocument.cookie = ''
    mockLocalStorage.getItem.mockReturnValue(null)
  })

  it('should handle complete login flow', async () => {
    const mockLoginResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      expires_in: 3600,
      username: 'admin'
    }

    const mockUser = {
      sub: 'user-id',
      username: 'admin',
      scope: 'admin'
    }

    // Mock login API
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockLoginResponse)
    })

    // Mock getCurrentUser API
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUser)
    })

    // Mock logout API
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: 'Logged out successfully' })
    })

    // 1. Login
    const loginResult = await login({ username: 'admin', password: 'admin123' })
    expect(loginResult.access_token).toBe('test-token')

    // 2. Store token
    storeToken(loginResult.access_token)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('voj_access_token', 'test-token')

    // 3. Get current user
    mockLocalStorage.getItem.mockReturnValue('test-token')
    const user = await getCurrentUser()
    expect(user).toEqual(mockUser)

    // 4. Store user
    storeUser(user)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('voj_user_info', JSON.stringify(mockUser))

    // 5. Check login status
    expect(isLoggedIn()).toBe(true)

    // 6. Get auth headers
    const headers = getAuthHeaders()
    expect(headers['Authorization']).toBe('Bearer test-token')

    // 7. Logout
    await logout()
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_access_token')
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('voj_user_info')
  })
})
