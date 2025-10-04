/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: [
      '@radix-ui/react-icons'
    ]
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl.replace(/\/$/, '')}/api/:path*`
      },
      {
        source: '/ws/:path*',
        destination: `${apiUrl.replace(/\/$/, '')}/ws/:path*`
      }
    ]
  },
  // Railway 배포 설정
  output: 'standalone'
}

module.exports = nextConfig


