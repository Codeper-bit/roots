// TEMPORARY. The backend has no authentication yet: stories require an
// owner_id, and content/reviews require a user id that already exists in the
// `users` table. Until Supabase Auth is integrated, the person using the app
// supplies an existing user id here. It is stored only in this browser.
// When real auth lands, replace getUserId() with the authenticated user's id.
import { useSyncExternalStore } from 'react'
import { isUuid } from '../utils/uuid'

const KEY = 'roots.userId'
const EVENT = 'roots:identity'

function read(): string | null {
  try {
    const value = window.localStorage.getItem(KEY)
    return value && isUuid(value) ? value : null
  } catch {
    return null
  }
}

let memoryFallback: string | null = null

export function getUserId(): string | null {
  return read() ?? memoryFallback
}

export function setUserId(value: string) {
  const trimmed = value.trim()
  if (!isUuid(trimmed)) throw new Error('That is not a valid UUID.')
  memoryFallback = trimmed
  try {
    window.localStorage.setItem(KEY, trimmed)
  } catch {
    /* storage unavailable: keep in memory for this tab */
  }
  window.dispatchEvent(new Event(EVENT))
}

export function clearUserId() {
  memoryFallback = null
  try {
    window.localStorage.removeItem(KEY)
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event(EVENT))
}

function subscribe(cb: () => void) {
  window.addEventListener(EVENT, cb)
  window.addEventListener('storage', cb)
  return () => {
    window.removeEventListener(EVENT, cb)
    window.removeEventListener('storage', cb)
  }
}

export function useUserId(): string | null {
  return useSyncExternalStore(subscribe, getUserId)
}
