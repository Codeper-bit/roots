import { Link } from '../../lib/router'
import type { ReviewStatus, Story } from '../../types'
import { formatDate } from '../../utils/formatDate'
import { languageName } from '../../utils/languages'
import { ReviewBadge, StoryStatusBadge } from '../ui/Badge'
import { Icon } from '../ui/Icon'
import { StoryArt } from './StoryArt'

export function StoryCard({
  story,
  transcriptReview,
}: {
  story: Story
  /** review status of the latest transcript, when it has been loaded. undefined = unknown, null = no transcript yet */
  transcriptReview?: ReviewStatus | null
}) {
  return (
    <article className="story-card">
      <Link to={`/stories/${story.id}`} className="story-card__link" aria-label={`Open ${story.title}`}>
        <div className="story-card__art">
          <StoryArt seed={story.id} />
          <span className="story-card__lang">{languageName(story.source_language)}</span>
        </div>
        <div className="story-card__body">
          <h3 className="story-card__title">{story.title}</h3>
          {story.description && <p className="story-card__desc">{story.description}</p>}
          <div className="story-card__meta">
            <StoryStatusBadge status={story.status} />
            {transcriptReview && <ReviewBadge status={transcriptReview} />}
            {transcriptReview === null && <span className="muted small">No transcript yet</span>}
          </div>
          <p className="story-card__foot">
            <span className="muted small">{formatDate(story.created_at)}</span>
            <span className="story-card__open">
              Open <Icon name="arrowRight" size={16} />
            </span>
          </p>
        </div>
      </Link>
    </article>
  )
}
