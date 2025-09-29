/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: [
      '@radix-ui/react-icons'
    ]
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://VojBac-Servi-hjiWLfezIKV1-104186311.ap-northeast-2.elb.amazonaws.com'
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
  }
}

module.exports = nextConfig


