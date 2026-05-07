const DEFAULT_API_URL = 'http://localhost:8000'

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, '')
}

export const API_BASE_URL = trimTrailingSlash(
  process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    DEFAULT_API_URL
)

export function apiUrl(path: string) {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function wsUrl(path: string, token?: string) {
  const url = new URL(path.startsWith('/') ? path : `/${path}`, API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  if (token) url.searchParams.set('token', token)
  return url.toString()
}
