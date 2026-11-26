import type { ReviewStatus } from '../../types'
import { ReviewBadge } from '../ui/Badge'

const EXPLAIN: Record<ReviewStatus, string> = {
  unreviewed: 'Nobody has confirmed this text yet. It may contain mistakes.',
  approved: 'A reviewer confirmed this text is accurate.',
  changes_requested: 'A reviewer asked for corrections before it can be approved.',
  rejected: 'A reviewer rejected this text.',
}

export function ReviewStatusLine({ status }: { status: ReviewStatus }) {
  return (
    <div className="review-status">
      <ReviewBadge status={status} />
      <span className="muted small">{EXPLAIN[status]}</span>
    </div>
  )
}
