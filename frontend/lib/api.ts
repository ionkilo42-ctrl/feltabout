const DEFAULT_API_URL = process.env.NEXT_PUBLIC_API_URL || ''

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, '')
}

export const API_BASE_URL = trimTrailingSlash(DEFAULT_API_URL)

export function apiUrl(path: string) {
  // When NEXT_PUBLIC_API_URL is empty (web proxy mode), use relative paths.
  // When set (mobile/explicit absolute), use absolute URLs.
  if (!API_BASE_URL) return path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function wsUrl(path: string, token?: string) {
  const url = new URL(path.startsWith('/') ? path : `/${path}`, API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  if (token) url.searchParams.set('token', token)
  return url.toString()
}
