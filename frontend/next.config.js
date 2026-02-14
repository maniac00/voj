/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // 프로덕션 빌드 시 ESLint 오류로 빌드가 중단되지 않도록 설정
    ignoreDuringBuilds: true,
  },
  experimental: {
    optimizePackageImports: [
      '@radix-ui/react-icons'
    ]
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ]
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    // HTTPS 강제 (프로덕션 환경에서만)
    const finalApiUrl = process.env.NODE_ENV === 'production' && apiUrl.startsWith('http://')
      ? apiUrl.replace('http://', 'https://')
      : apiUrl

    return [
      {
        source: '/api/:path*',
        destination: `${finalApiUrl.replace(/\/$/, '')}/api/:path*`
      },
      {
        source: '/ws/:path*',
        destination: `${finalApiUrl.replace(/\/$/, '')}/ws/:path*`
      }
    ]
  },
  // Railway 배포 설정
  output: 'standalone'
}

module.exports = nextConfig
