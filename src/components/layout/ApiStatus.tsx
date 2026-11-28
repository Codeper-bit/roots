import { useEffect, useState } from 'react'
import { checkHealth } from '../../api/health'
import { API_BASE_URL } from '../../api/client'
import { describeError } from '../../utils/errors'

type Status = { state: 'checking' } | { state: 'online' } | { state: 'offline'; reason: string }

export function ApiStatus() {
  const [status, setStatus] = useState<Status>({ state: 'checking' })

  useEffect(() => {
    let cancelled = false
    let failures = 0
    const run = () => {
      checkHealth()
        .then(() => {
          failures = 0
          if (!cancelled) setStatus({ state: 'online' })
        })
        .catch((err) => {
          // A single missed check (server reload, brief network blip) shouldn't flash "unreachable".
          failures += 1
          if (!cancelled && failures >= 2) setStatus({ state: 'offline', reason: describeError(err) })
        })
    }
    run()
    const id = window.setInterval(run, 15000)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  const label =
    status.state === 'checking' ? 'Checking server' : status.state === 'online' ? 'Server connected' : 'Server unreachable'
  const title = status.state === 'offline' ? `${API_BASE_URL}: ${status.reason}` : API_BASE_URL

  return (
    <span className={`api-status api-status--${status.state}`} title={title} role="status">
      <span className="api-status__dot" aria-hidden="true" />
      <span className="api-status__label">{label}</span>
    </span>
  )
}
