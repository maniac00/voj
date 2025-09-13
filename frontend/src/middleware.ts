import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// 보호된 경로 목록
const protectedPaths = [
  '/books',
  '/dashboard',
  '/admin'
]

// 인증 경로 목록
const authPaths = [
  '/login',
  '/callback'
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // 토큰 확인 (localStorage는 서버에서 접근 불가하므로 쿠키 사용)
  const token = request.cookies.get('voj_access_token')?.value
  const isAuthenticated = !!token

  // 루트 경로 처리
  if (pathname === '/') {
    if (isAuthenticated) {
      return NextResponse.redirect(new URL('/books', request.url))
    } else {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // 보호된 경로 접근 시 인증 확인
  const isProtectedPath = protectedPaths.some(path => 
    pathname.startsWith(path)
  )
  
  if (isProtectedPath && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('returnUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // 이미 로그인된 사용자가 인증 페이지 접근 시 리디렉션
  const isAuthPath = authPaths.some(path => 
    pathname.startsWith(path)
  )
  
  if (isAuthPath && isAuthenticated) {
    const returnUrl = request.nextUrl.searchParams.get('returnUrl')
    const redirectTo = returnUrl || '/books'
    return NextResponse.redirect(new URL(redirectTo, request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}
