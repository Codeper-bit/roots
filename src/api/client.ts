import { supabase } from '../lib/supabase'

// Central HTTP client. The base URL is read in exactly one place.

export const API_BASE_URL: string = (
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://127.0.0.1:8000'
).replace(/\/+$/, '')

export type ApiErrorKind =
  | 'network'
  | 'unauthorized' // 401
  | 'validation' // 400 / 422
  | 'consent' // 403
  | 'not_found' // 404
  | 'too_large' // 413
  | 'unsupported' // 415
  | 'unavailable' // 503
  | 'server' // 5xx
  | 'http'

export class ApiError extends Error {
  readonly status: number
  readonly kind: ApiErrorKind
  /** field name -> message, parsed from FastAPI 422 responses */
  readonly fieldErrors: Record<string, string>

  constructor(
    message: string,
    status: number,
    kind: ApiErrorKind,
    fieldErrors: Record<string, string> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.kind = kind
    this.fieldErrors = fieldErrors
  }
}

interface FastApiValidationItem {
  loc?: Array<string | number>
  msg?: string
}

function kindForStatus(status: number): ApiErrorKind {
  if (status === 401) return 'unauthorized'
  if (status === 400 || status === 422) return 'validation'
  if (status === 403) return 'consent'
  if (status === 404) return 'not_found'
  if (status === 413) return 'too_large'
  if (status === 415) return 'unsupported'
  if (status === 503) return 'unavailable'
  if (status >= 500) return 'server'
  return 'http'
}

function parseErrorBody(body: unknown, status: number): ApiError {
  const kind = kindForStatus(status)
  let message = ''
  const fieldErrors: Record<string, string> = {}

  const detail =
    body && typeof body === 'object' && 'detail' in body
      ? (body as { detail: unknown }).detail
      : undefined

  if (typeof detail === 'string') {
    message = detail
  } else if (Array.isArray(detail)) {
    const parts: string[] = []
    for (const item of detail as FastApiValidationItem[]) {
      const field = item.loc && item.loc.length > 0 ? String(item.loc[item.loc.length - 1]) : ''
      const msg = item.msg ?? 'Invalid value'
      if (field && field !== 'body') fieldErrors[field] = msg
      parts.push(field && field !== 'body' ? `${field}: ${msg}` : msg)
    }
    message = parts.join('. ')
  } else if (detail && typeof detail === 'object') {
    // e.g. /health 503 -> { status, database }
    message = Object.entries(detail as Record<string, unknown>)
      .map(([k, v]) => `${k}: ${String(v)}`)
      .join(', ')
  }

  if (!message) message = `Request failed with status ${status}.`
  return new ApiError(message, status, kind, fieldErrors)
}

function networkError(): ApiError {
  return new ApiError(
    `Can't reach the Roots server at ${API_BASE_URL}. Check your internet connection and that the ` +
      `backend is running. (Errors the server reports itself, such as a failed transcription, are ` +
      `shown with their own message instead.)`,
    0,
    'network',
  )
}

function abortError(): DOMException {
  return new DOMException('The request was cancelled', 'AbortError')
}

/**
 * The current Supabase access token, or null when signed out. Never throws:
 * a storage hiccup must not turn into a confusing failure on every request.
 */
async function getAccessToken(forceRefresh = false): Promise<string | null> {
  try {
    if (forceRefresh) {
      const { data } = await supabase.auth.refreshSession()
      return data.session?.access_token ?? null
    }
    const { data } = await supabase.auth.getSession()
    return data.session?.access_token ?? null
  } catch {
    return null
  }
}

function buildUrl(path: string, query?: Record<string, string | number | undefined>): string {
  const url = `${API_BASE_URL}${path}`
  if (!query) return url
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return qs ? `${url}?${qs}` : url
}

export interface RequestOptions {
  query?: Record<string, string | number | undefined>
  json?: unknown
  signal?: AbortSignal
}

export async function request<T>(
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(path, options.query)
  const body = options.json !== undefined ? JSON.stringify(options.json) : undefined

  const send = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (token) headers.Authorization = `Bearer ${token}`
    try {
      return await fetch(url, { method, headers, body, signal: options.signal })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') throw err
      throw networkError()
    }
  }

  let response = await send(await getAccessToken())

  // An access token can expire while the page is open. Refresh once and retry.
  if (response.status === 401) {
    const refreshed = await getAccessToken(true)
    if (refreshed) response = await send(refreshed)
  }

  if (response.status === 204) return undefined as T

  let payload: unknown = null
  const text = await response.text()
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = null
    }
  }

  if (!response.ok) throw parseErrorBody(payload, response.status)
  return payload as T
}

export const get = <T>(path: string, options?: RequestOptions) => request<T>('GET', path, options)
export const post = <T>(path: string, json?: unknown, options?: RequestOptions) =>
  request<T>('POST', path, { ...options, json })
export const patch = <T>(path: string, json?: unknown, options?: RequestOptions) =>
  request<T>('PATCH', path, { ...options, json })

/**
 * Multipart upload with progress. Uses XMLHttpRequest because fetch cannot
 * report upload progress. The Content-Type header is deliberately NOT set so
 * the browser adds the multipart boundary itself.
 */
export function uploadForm<T>(
  path: string,
  form: FormData,
  onProgress?: (fraction: number) => void,
  signal?: AbortSignal,
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    if (signal?.aborted) {
      reject(abortError())
      return
    }

    const xhr = new XMLHttpRequest()
    let settled = false

    const settle = (action: () => void) => {
      if (settled) return
      settled = true
      signal?.removeEventListener('abort', onAbort)
      action()
    }
    const onAbort = () => {
      xhr.abort()
      settle(() => reject(abortError()))
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) onProgress(event.loaded / event.total)
    }
    xhr.onerror = () => settle(() => reject(networkError()))
    xhr.ontimeout = () => settle(() => reject(networkError()))
    xhr.onabort = () => settle(() => reject(abortError()))
    xhr.onload = () =>
      settle(() => {
        let payload: unknown = null
        if (xhr.responseText) {
          try {
            payload = JSON.parse(xhr.responseText)
          } catch {
            payload = null
          }
        }
        if (xhr.status >= 200 && xhr.status < 300) resolve(payload as T)
        else reject(parseErrorBody(payload, xhr.status))
      })

    signal?.addEventListener('abort', onAbort, { once: true })

    // The token is fetched first, then the request is opened and sent in one
    // go, so an abort can never land between open() and send().
    void getAccessToken().then((token) => {
      if (settled) return
      xhr.open('POST', buildUrl(path))
      xhr.setRequestHeader('Accept', 'application/json')
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(form)
    })
  })
}
