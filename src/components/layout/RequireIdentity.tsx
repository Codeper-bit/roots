import type { ReactNode } from 'react'
import { useAuth } from '../../auth/AuthContext'
import { Link } from '../../lib/router'

export function RequireIdentity({ children }: { children: (userId: string) => ReactNode }) {
  const { profileId, loading } = useAuth()
  if (loading) return <div className="card card--pad"><p className="muted">Loading your Roots account…</p></div>
  if (profileId) return <>{children(profileId)}</>
  return <div className="card card--pad identity-gate stack"><p className="eyebrow">Sign in required</p><h2 className="card__title">Sign in to continue</h2><p className="muted">Your Roots workspace is connected to your account.</p><div className="row"><Link className="btn btn--primary" to="/login">Sign in</Link><Link className="btn btn--secondary" to="/register">Create account</Link></div></div>
}
