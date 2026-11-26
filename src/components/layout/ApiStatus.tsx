import { useEffect, useState } from 'react'
import { checkHealth } from '../../api/health'
import { API_BASE_URL } from '../../api/client'
import { describeError } from '../../utils/errors'

type Status = { state: 'checking' } | { state: 'online' } | { state: 'offline'; reason: string }

export function ApiStatus() {
  const [status, setStatus] = useState<Status>({ state: 'checking' })

  useEffect(() => {
    let cancelled = false
    const run = () => {
      checkHealth()
        .then(() => !cancelled && setStatus({ state: 'online' }))
        .catch((err) => !cancelled && setStatus({ state: 'offline', reason: describeError(err) }))
    }
    run()
    const id = window.setInterval(run, 30000)
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
