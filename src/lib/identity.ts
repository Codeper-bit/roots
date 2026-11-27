import { useSyncExternalStore } from 'react'

const EVENT = 'roots:identity'
let profileId: string | null = null

export function getUserId(): string | null { return profileId }
export function setUserId(value: string) { profileId = value; window.dispatchEvent(new Event(EVENT)) }
export function clearUserId() { profileId = null; window.dispatchEvent(new Event(EVENT)) }
function subscribe(cb: () => void) { window.addEventListener(EVENT, cb); return () => window.removeEventListener(EVENT, cb) }
export function useUserId(): string | null { return useSyncExternalStore(subscribe, getUserId, () => null) }
