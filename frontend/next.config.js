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
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

    // 디버깅: 빌드 시점의 환경변수 로그
    console.log('🔧 [next.config.js] NEXT_PUBLIC_API_URL:', apiUrl)

    // HTTPS 강제 (프로덕션 환경에서만)
    const finalApiUrl = process.env.NODE_ENV === 'production' && apiUrl.startsWith('http://')
      ? apiUrl.replace('http://', 'https://')
      : apiUrl

    console.log('🔧 [next.config.js] Final API URL:', finalApiUrl)

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


