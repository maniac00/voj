/**
 * 로그인 페이지 테스트
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { login, storeToken, storeUser, getCurrentUser } from '@/lib/auth/simple-auth'
import LoginPage from './page'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/lib/auth/simple-auth', () => ({
  login: jest.fn(),
  storeToken: jest.fn(),
  storeUser: jest.fn(),
  getCurrentUser: jest.fn(),
}))

const mockPush = jest.fn()
const mockGet = jest.fn()
const mockRefreshUser = jest.fn()

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    
    ;(useSearchParams as jest.Mock).mockReturnValue({
      get: mockGet,
    })
    
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      refreshUser: mockRefreshUser,
    })
  })

  it('should render login form', () => {
    render(<LoginPage />)
    
    expect(screen.getByText('관리자 로그인')).toBeInTheDocument()
    expect(screen.getByText('VOJ Audiobooks 관리자 시스템')).toBeInTheDocument()
    expect(screen.getByLabelText('사용자명')).toBeInTheDocument()
    expect(screen.getByLabelText('비밀번호')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '로그인' })).toBeInTheDocument()
    expect(screen.getByText('기본 계정: admin / admin123')).toBeInTheDocument()
  })

  it('should redirect if already authenticated', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      refreshUser: mockRefreshUser,
    })
    
    mockGet.mockReturnValue(null)
    
    render(<LoginPage />)
    
    expect(mockPush).toHaveBeenCalledWith('/books')
  })

  it('should redirect to returnUrl if authenticated', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      refreshUser: mockRefreshUser,
    })
    
    mockGet.mockReturnValue('/dashboard')
    
    render(<LoginPage />)
    
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('should handle successful login', async () => {
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
    
    ;(login as jest.Mock).mockResolvedValue(mockLoginResponse)
    ;(getCurrentUser as jest.Mock).mockResolvedValue(mockUser)
    mockGet.mockReturnValue(null)
    
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    const loginButton = screen.getByRole('button', { name: '로그인' })
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } })
    fireEvent.change(passwordInput, { target: { value: 'admin123' } })
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        username: 'admin',
        password: 'admin123'
      })
    })
    
    expect(storeToken).toHaveBeenCalledWith('test-token')
    expect(getCurrentUser).toHaveBeenCalled()
    expect(storeUser).toHaveBeenCalledWith(mockUser)
    expect(mockRefreshUser).toHaveBeenCalled()
    expect(mockPush).toHaveBeenCalledWith('/books')
  })

  it('should handle login with returnUrl', async () => {
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
    
    ;(login as jest.Mock).mockResolvedValue(mockLoginResponse)
    ;(getCurrentUser as jest.Mock).mockResolvedValue(mockUser)
    mockGet.mockReturnValue('/dashboard')
    
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    const loginButton = screen.getByRole('button', { name: '로그인' })
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } })
    fireEvent.change(passwordInput, { target: { value: 'admin123' } })
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('should display error on login failure', async () => {
    ;(login as jest.Mock).mockRejectedValue(new Error('Invalid username or password'))
    
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    const loginButton = screen.getByRole('button', { name: '로그인' })
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } })
    fireEvent.change(passwordInput, { target: { value: 'wrong' } })
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid username or password')).toBeInTheDocument()
    })
    
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should show loading state during login', async () => {
    ;(login as jest.Mock).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    const loginButton = screen.getByRole('button', { name: '로그인' })
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } })
    fireEvent.change(passwordInput, { target: { value: 'admin123' } })
    fireEvent.click(loginButton)
    
    expect(screen.getByText('로그인 중...')).toBeInTheDocument()
    expect(loginButton).toBeDisabled()
  })

  it('should require username and password', () => {
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    
    expect(usernameInput).toHaveAttribute('required')
    expect(passwordInput).toHaveAttribute('required')
  })

  it('should have proper accessibility attributes', () => {
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    
    expect(usernameInput).toHaveAttribute('autoComplete', 'username')
    expect(passwordInput).toHaveAttribute('autoComplete', 'current-password')
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('should handle form submission with Enter key', async () => {
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
    
    ;(login as jest.Mock).mockResolvedValue(mockLoginResponse)
    ;(getCurrentUser as jest.Mock).mockResolvedValue(mockUser)
    
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } })
    fireEvent.change(passwordInput, { target: { value: 'admin123' } })
    fireEvent.keyDown(passwordInput, { key: 'Enter', code: 'Enter' })
    
    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        username: 'admin',
        password: 'admin123'
      })
    })
  })

  it('should clear error when user starts typing', async () => {
    ;(login as jest.Mock).mockRejectedValue(new Error('Invalid credentials'))
    
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText('사용자명')
    const passwordInput = screen.getByLabelText('비밀번호')
    const loginButton = screen.getByRole('button', { name: '로그인' })
    
    // Trigger error
    fireEvent.change(usernameInput, { target: { value: 'admin' } })
    fireEvent.change(passwordInput, { target: { value: 'wrong' } })
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
    
    // Clear error by typing
    ;(login as jest.Mock).mockClear()
    fireEvent.change(passwordInput, { target: { value: 'admin123' } })
    
    expect(screen.queryByText('Invalid credentials')).not.toBeInTheDocument()
  })
})
