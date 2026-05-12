const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || ''

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, '')
}

export const API_BASE_URL = trimTrailingSlash(DEFAULT_API_URL)

export function apiUrl(path: string) {
  const normalized = path.startsWith('/') ? path : `/${path}`

  // Browser requests in the web app should stay same-origin and let Next.js proxy
  // them to the backend. This avoids direct browser calls to Docker-only hostnames.
  if (typeof window !== 'undefined') {
    return `/api${normalized}`
  }

  if (!API_BASE_URL) {
    return normalized
  }

  return `${API_BASE_URL}${normalized}`
}

export function wsUrl(path: string, token?: string) {
  const url = new URL(path.startsWith('/') ? path : `/${path}`, API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  if (token) url.searchParams.set('token', token)
  return url.toString()
}
