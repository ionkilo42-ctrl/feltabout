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
  
  // Proxy browser /api/* requests to the backend
  async rewrites() {
    return [
      {
        // NextAuth routes - handled by Next.js (no proxy needed)
        source: '/api/auth/providers',
        destination: '/api/auth/providers',
      },
      {
        // NextAuth session - handled by Next.js
        source: '/api/auth/session',
        destination: '/api/auth/session',
      },
      {
        // NextAuth callback - handled by Next.js
        source: '/api/auth/callback/:path*',
        destination: '/api/auth/callback/:path*',
      },
      {
        // NextAuth signin - handled by Next.js
        source: '/api/auth/signin/:path*',
        destination: '/api/auth/signin/:path*',
      },
      {
        // NextAuth CSRF - handled by Next.js
        source: '/api/auth/csrf',
        destination: '/api/auth/csrf',
      },
      {
        // NextAuth _log (for error logging) - handled by Next.js
        source: '/api/auth/_log',
        destination: '/api/auth/_log',
      },
      {
        // All other /api/* routes → proxy to backend
        // e.g. /api/auth/magic-link-request → http://api:8000/auth/magic-link-request
        source: '/api/:path*',
        destination: `${proxyTarget}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;