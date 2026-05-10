const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || ''

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, '')
}

export const API_BASE_URL = trimTrailingSlash(DEFAULT_API_URL)

export function apiUrl(path: string) {
  // Proxy mode (web/ngrok): always prefix /api since Next.js rewrite maps /api/* → backend
  if (!API_BASE_URL) {
    const normalized = path.startsWith('/') ? path : `/${path}`
    return `/api${normalized}`
  }
  // Absolute URL mode (mobile/explicit env): use full URL
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function wsUrl(path: string, token?: string) {
  const url = new URL(path.startsWith('/') ? path : `/${path}`, API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  if (token) url.searchParams.set('token', token)
  return url.toString()
}
