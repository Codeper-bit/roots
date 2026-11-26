import { Link } from '../../lib/router'
import type { ContentVersion, Story } from '../../types'
import { formatDate } from '../../utils/formatDate'
import { languageName } from '../../utils/languages'
import { OriginBadge, ReviewBadge } from '../ui/Badge'
import { ReviewActions } from './ReviewActions'

const TYPE_LABEL = { transcript: 'Transcript', translation: 'Translation', interpretation: 'Interpretation' } as const

export function ReviewCard({
  story,
  version,
  reviewerId,
  onDone,
}: {
  story: Story
  version: ContentVersion
  reviewerId: string
  onDone: () => void
}) {
  return (
    <article className="review-card">
      <header className="review-card__head">
        <div>
          <Link className="review-card__story" to={`/stories/${story.id}`}>
            {story.title}
          </Link>
          <p className="muted small">
            {TYPE_LABEL[version.content_type]} · {languageName(version.language_code)} · version {version.version_number} ·{' '}
            {formatDate(version.created_at)}
          </p>
        </div>
        <div className="row row--wrap">
          <OriginBadge origin={version.origin} />
          <ReviewBadge status={version.review_status} />
        </div>
      </header>
      <p className="review-card__preview">{version.content}</p>
      <footer className="review-card__foot">
        <ReviewActions version={version} reviewerId={reviewerId} onDone={onDone} compact />
        <Link className="link" to={`/stories/${story.id}/review?version=${version.id}`}>
          Open full text
        </Link>
      </footer>
    </article>
  )
}
