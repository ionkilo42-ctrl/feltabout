/**
 * @type {import('next').NextConfig}
 * 
 * Feltabout Frontend Configuration
 * 
 * Environment variables:
 * - NEXT_PUBLIC_API_URL: server-side backend target for proxy rewrites
 *
 * Browser requests should stay same-origin and use /api/*.
 * In Docker, the Next server can reach the backend at http://api:8000.
 * In host-side local dev, it should proxy to http://localhost:8000.
 */
const proxyTarget =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === 'development'
    ? 'http://localhost:8000'
    : 'http://api:8000')

const nextConfig = {
  output: 'standalone',
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  
  // API URL configuration
  env: {
    // Keep server-side target available when needed, but browser calls still use /api.
    NEXT_PUBLIC_API_URL: proxyTarget,
  },
  
  // Proxy all browser /api/* requests through the Next.js server.
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${proxyTarget}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
