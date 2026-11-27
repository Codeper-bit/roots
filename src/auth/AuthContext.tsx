import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { clearUserId, setUserId } from '../lib/identity'
import { API_BASE_URL } from '../api/client'

interface AuthContextValue {
  session: Session | null
  user: User | null
  profileId: string | null
  loading: boolean
  profileError: string | null
  signOut: () => Promise<void>
  refreshProfile: (displayName?: string) => Promise<string>
}
const AuthContext = createContext<AuthContextValue | null>(null)

async function syncProfile(session: Session, displayName?: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/auth/profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${session.access_token}`,
    },
    body: JSON.stringify({
      display_name:
        displayName?.trim() ||
        session.user.user_metadata?.display_name ||
        session.user.email?.split('@')[0] ||
        'Roots user',
    }),
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = payload && typeof payload.detail === 'string' ? payload.detail : null
    throw new Error(detail || `Could not create Roots profile (${response.status}).`)
  }
  if (!payload || typeof payload.id !== 'string') {
    throw new Error('The Roots server returned an invalid profile response.')
  }
  return payload.id
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [profileId, setProfileId] = useState<string | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function loadProfile(nextSession: Session, displayName?: string) {
    setProfileError(null)
    try {
      const id = await syncProfile(nextSession, displayName)
      setProfileId(id)
      setUserId(id)
      return id
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not load your Roots profile.'
      setProfileId(null)
      clearUserId()
      setProfileError(message)
      throw new Error(message)
    }
  }

  useEffect(() => {
    let alive = true

    void supabase.auth.getSession().then(async ({ data, error }) => {
      if (!alive) return
      if (error) setProfileError(error.message)
      setSession(data.session)
      if (data.session) {
        try {
          const id = await syncProfile(data.session)
          if (alive) {
            setProfileId(id)
            setUserId(id)
            setProfileError(null)
          }
        } catch (err) {
          if (alive) {
            setProfileId(null)
            clearUserId()
            setProfileError(err instanceof Error ? err.message : 'Could not load your Roots profile.')
          }
        }
      } else {
        setProfileId(null)
        clearUserId()
      }
      if (alive) setLoading(false)
    })

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!alive) return
      setSession(nextSession)
      if (!nextSession) {
        setProfileId(null)
        setProfileError(null)
        clearUserId()
        setLoading(false)
        return
      }
      // Supabase recommends keeping network requests outside its auth callback.
      queueMicrotask(() => {
        void syncProfile(nextSession)
          .then((id) => {
            if (!alive) return
            setProfileId(id)
            setUserId(id)
            setProfileError(null)
          })
          .catch((err) => {
            if (!alive) return
            setProfileId(null)
            clearUserId()
            setProfileError(err instanceof Error ? err.message : 'Could not load your Roots profile.')
          })
          .finally(() => {
            if (alive) setLoading(false)
          })
      })
    })

    return () => {
      alive = false
      listener.subscription.unsubscribe()
    }
  }, [])

  const value = useMemo<AuthContextValue>(() => ({
    session,
    user: session?.user ?? null,
    profileId,
    loading,
    profileError,
    signOut: async () => {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      setSession(null)
      setProfileId(null)
      setProfileError(null)
      clearUserId()
    },
    refreshProfile: async (displayName?: string) => {
      const { data, error } = await supabase.auth.getSession()
      if (error) throw error
      if (!data.session) throw new Error('Your session has expired. Please sign in again.')
      setSession(data.session)
      return loadProfile(data.session, displayName)
    },
  }), [session, profileId, loading, profileError])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
