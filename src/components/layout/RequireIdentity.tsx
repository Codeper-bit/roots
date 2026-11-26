import type { ReactNode } from 'react'
import { useUserId } from '../../lib/identity'
import { IdentityForm } from './IdentityForm'

export function RequireIdentity({ children }: { children: (userId: string) => ReactNode }) {
  const userId = useUserId()
  if (userId) return <>{children(userId)}</>
  return (
    <div className="card card--pad identity-gate">
      <p className="eyebrow">One thing first</p>
      <h2 className="card__title">Choose who you are working as</h2>
      <IdentityForm />
    </div>
  )
}
