import { ButtonLink } from '../components/ui/Button'
import { EmptyState } from '../components/ui/States'

export function NotFoundPage() {
  return (
    <EmptyState
      icon="library"
      title="We couldn’t find that page"
      action={<ButtonLink to="/dashboard">Back to your stories</ButtonLink>}
    >
      The link may be out of date.
    </EmptyState>
  )
}
