import type { ReactNode } from 'react'
import { describeError } from '../../utils/errors'
import { Button } from './Button'
import { Icon, type IconName } from './Icon'

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <span className="spinner spinner--lg" aria-hidden="true" />
      <p className="state__text">{label}</p>
    </div>
  )
}

export function EmptyState({
  icon = 'library',
  title,
  children,
  action,
}: {
  icon?: IconName
  title: string
  children?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="state state--empty">
      <span className="state__icon">
        <Icon name={icon} size={26} />
      </span>
      <h3 className="state__title">{title}</h3>
      {children && <p className="state__text">{children}</p>}
      {action && <div className="state__action">{action}</div>}
    </div>
  )
}

export function ErrorState({
  error,
  title = 'Something went wrong',
  onRetry,
}: {
  error: unknown
  title?: string
  onRetry?: () => void
}) {
  return (
    <div className="state state--error" role="alert">
      <span className="state__icon state__icon--error">
        <Icon name="alert" size={26} />
      </span>
      <h3 className="state__title">{title}</h3>
      <p className="state__text">{describeError(error)}</p>
      {onRetry && (
        <div className="state__action">
          <Button variant="secondary" icon="refresh" onClick={onRetry}>
            Try again
          </Button>
        </div>
      )}
    </div>
  )
}

export function Notice({
  tone = 'info',
  title,
  children,
  action,
}: {
  tone?: 'info' | 'warning' | 'error' | 'success'
  title?: string
  children?: ReactNode
  action?: ReactNode
}) {
  const icon: IconName = tone === 'success' ? 'checkCircle' : tone === 'info' ? 'info' : 'alert'
  return (
    <div className={`notice notice--${tone}`} role={tone === 'error' ? 'alert' : 'note'}>
      <Icon name={icon} size={20} />
      <div className="notice__body">
        {title && <strong className="notice__title">{title}</strong>}
        {children && <div className="notice__text">{children}</div>}
        {action && <div className="notice__action">{action}</div>}
      </div>
    </div>
  )
}
