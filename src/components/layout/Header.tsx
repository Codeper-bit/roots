import { useAuth } from '../../auth/AuthContext'
import { Link } from '../../lib/router'
import { Wordmark } from '../ui/Icon'
import { ApiStatus } from './ApiStatus'
import { Button } from '../ui/Button'

export function Header() {
  const { user, signOut } = useAuth()
  return <header className="topbar"><Link to="/" className="topbar__brand" aria-label="Roots home"><Wordmark size={20} /></Link><div className="topbar__spacer" /><ApiStatus /><span className="muted small">{user?.email}</span><Button size="sm" variant="ghost" onClick={() => void signOut()}>Sign out</Button></header>
}
