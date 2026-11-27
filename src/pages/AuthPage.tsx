import { useEffect, useState, type FormEvent } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../auth/AuthContext'
import { Link, useNavigate } from '../lib/router'
import { Wordmark } from '../components/ui/Icon'
import { Input } from '../components/ui/Field'
import { Button } from '../components/ui/Button'

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const register = mode === 'register'
  const navigate = useNavigate()
  const { session, profileId, profileError, loading, refreshProfile } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!loading && session && profileId) navigate('/dashboard', { replace: true })
  }, [loading, session, profileId, navigate])

  async function finishProfile(displayName?: string) {
    await refreshProfile(displayName)
    navigate('/dashboard', { replace: true })
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    try {
      if (register) {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { data: { display_name: name.trim() } },
        })
        if (signUpError) throw signUpError
        if (!data.session) {
          setMessage('Account created. If email confirmation is enabled, confirm your address before signing in.')
          return
        }
        await finishProfile(name.trim())
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        })
        if (signInError) throw signInError
        // Fetch the current session and create/retrieve its Roots profile before navigating.
        await finishProfile()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function retryProfile() {
    setBusy(true)
    setError('')
    try {
      await finishProfile()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load your Roots profile.')
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <main className="auth-page"><section className="auth-card"><p>Loading your account…</p></section></main>

  return <main className="auth-page"><section className="auth-card">
    <Link to="/" className="auth-brand"><Wordmark size={24} /></Link>
    <p className="eyebrow">A family archive for voices and languages</p>
    <h1>{register ? 'Create your Roots account' : 'Welcome back'}</h1>
    <p className="muted">{register ? 'Start preserving the stories your family carries.' : 'Sign in to continue preserving your family stories.'}</p>

    {session && !profileId ? <div className="stack">
      <p className="notice" role="status">You're signed in, but Roots could not finish setting up your workspace.</p>
      {(profileError || error) && <p className="field__error" role="alert">{error || profileError}</p>}
      <Button type="button" size="lg" loading={busy} onClick={retryProfile}>Retry workspace setup</Button>
      <Button type="button" variant="secondary" onClick={async () => { await supabase.auth.signOut(); navigate('/login', { replace: true }) }}>Sign out</Button>
    </div> : <form className="stack" onSubmit={submit}>
      {register && <Input label="Your name" value={name} onChange={e => setName(e.target.value)} autoComplete="name" required minLength={2} />}
      <Input label="Email address" type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" required />
      <div className="stack stack--xs">
        <Input label="Password" type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} autoComplete={register ? 'new-password' : 'current-password'} minLength={8} required />
        <label className="auth-show"><input type="checkbox" checked={showPassword} onChange={e => setShowPassword(e.target.checked)} /> Show password</label>
      </div>
      {error && <p className="field__error" role="alert">{error}</p>}
      {message && <p className="notice" role="status">{message}</p>}
      <Button type="submit" size="lg" loading={busy}>{register ? 'Create account' : 'Sign in'}</Button>
    </form>}

    {!session && <p className="auth-switch">{register ? 'Already have an account?' : 'New to Roots?'} <Link className="link" to={register ? '/login' : '/register'}>{register ? 'Sign in' : 'Create an account'}</Link></p>}
    <p className="muted small">Your account does not replace the storyteller’s permission to record or transcribe their story.</p>
  </section></main>
}
