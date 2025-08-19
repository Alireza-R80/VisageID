/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy API to backend during dev to keep same-origin cookies
    const backend = process.env.BACKEND_ORIGIN || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${backend}/:path*`,
      },
      {
        source: '/oauth/:path*',
        destination: `${backend}/oauth/:path*`,
      },
    ]
  },
}

module.exports = nextConfig;
