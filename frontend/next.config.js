/**
 * @type {import('next').NextConfig}
 * 
 * Feltabout Frontend Configuration
 * 
 * Environment variables:
 * - NEXT_PUBLIC_API_URL: API base URL (defaults to /api for proxy mode)
 * 
 * In Docker, NEXT_PUBLIC_API_URL is set to http://api:8000
 * In local dev without NEXT_PUBLIC_API_URL, uses Next.js rewrites to proxy /api/* to localhost:8000
 */
const nextConfig = {
  output: 'standalone',
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  
  // API URL configuration
  env: {
    // Make NEXT_PUBLIC_API_URL available at build time
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },
  
  // Development/Docker proxy configuration
  // Rewrites /api/* to the backend API for internal routing
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    
    // If API URL is explicitly set to localhost/empty proxy mode,
    // use Next.js internal rewrites for /api/* routing
    if (apiUrl && !apiUrl.startsWith('http://localhost') && !apiUrl.startsWith('http://127.0.0.1')) {
      // External absolute URL mode (mobile/explicit env): use direct calls
      return [];
    }
    
    // Docker internal network or local dev proxy:
    // Use Next.js rewrites to proxy /api/* to api service
    return [
      {
        source: '/api/:path*',
        destination: 'http://api:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;