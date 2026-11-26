import { useState } from 'react'
import { listContentVersions } from '../api/content'
import { listReviewsForVersion } from '../api/reviews'
import { StoryScope, type StoryContext } from '../components/layout/StoryScope'
import { ReviewActions } from '../components/review/ReviewActions'
import { ReviewStatusLine } from '../components/review/ReviewStatus'
import { TranscriptPane } from '../components/transcription/TranscriptPane'
import { Badge, OriginBadge, ReviewBadge } from '../components/ui/Badge'
import { ButtonLink } from '../components/ui/Button'
import { EmptyState, ErrorState, LoadingState, Notice } from '../components/ui/States'
import { useAsync } from '../hooks/useAsync'
import { Link, navigate, useParams, useSearchParams } from '../lib/router'
import { updateWorkflow } from '../lib/workflow'
import { formatDateTime } from '../utils/formatDate'
import { languageName } from '../utils/languages'
import { shortId } from '../utils/uuid'

export function ReviewPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="review">
      {(ctx) => <ReviewBody ctx={ctx} />}
    </StoryScope>
  )
}

const DECISION_LABEL = { approved: 'Approved', changes_requested: 'Changes requested', rejected: 'Rejected' } as const

function ReviewBody({ ctx }: { ctx: StoryContext }) {
  const { story, ownerId } = ctx
  const wanted = useSearchParams().get('version')
  const versionsState = useAsync((signal) => listContentVersions(story.id, signal), [story.id])
  const [dirty, setDirty] = useState(false)

  const versions = versionsState.data ?? []
  const transcripts = versions
    .filter((v) => v.content_type === 'transcript')
    .sort((a, b) => b.created_at.localeCompare(a.created_at) || b.version_number - a.version_number)
  const selected =
    (wanted ? versions.find((v) => v.id === wanted) : undefined) ??
    transcripts.find((v) => v.language_code === story.source_language) ??
    transcripts[0] ??
    null

  const reviews = useAsync(
    async (signal) => (selected ? listReviewsForVersion(selected.id, signal) : []),
    [selected?.id],
  )

  if (versionsState.loading && !versionsState.data) return <LoadingState label="Opening the review…" />
  if (versionsState.error && !versionsState.data) {
    return <ErrorState error={versionsState.error} title="We couldn’t load the transcript" onRetry={versionsState.reload} />
  }
  if (!selected) {
    return (
      <EmptyState
        icon="fileAudio"
        title="Nothing to review yet"
        action={<ButtonLink to={`/stories/${story.id}/transcribe`}>Go to transcription</ButtonLink>}
      >
        A transcript has to exist before it can be reviewed.
      </EmptyState>
    )
  }

  const sameKind = versions
    .filter((v) => v.content_type === selected.content_type && v.language_code === selected.language_code)
    .sort((a, b) => b.version_number - a.version_number)
  const newest = sameKind[0]
  const isOlder = newest && newest.id !== selected.id

  return (
    <div className="review-layout">
      <div className="stack">
        {isOlder && (
          <Notice
            tone="warning"
            title="You’re looking at an older version"
            action={
              <Link className="link" to={`/stories/${story.id}/review?version=${newest.id}`}>
                Go to the latest (version {newest.version_number})
              </Link>
            }
          >
            Version {selected.version_number} has been replaced by a newer one.
          </Notice>
        )}
        <section className="card card--pad stack" aria-label="Transcript to review">
          <div className="section-head">
            <h2 className="card__title">
              {selected.content_type === 'transcript' ? 'Transcript' : selected.content_type} · {languageName(selected.language_code)}
            </h2>
            <div className="row row--wrap">
              <OriginBadge origin={selected.origin} />
              <Badge>Version {selected.version_number}</Badge>
            </div>
          </div>
          {selected.origin === 'ai_generated' && (
            <Notice tone="warning" title="Written by AI, not yet confirmed">
              Read it closely. Fix any word that isn’t what the storyteller said. Only a person can
              confirm it is true.
            </Notice>
          )}
          <TranscriptPane
            version={selected}
            userId={ownerId}
            onDirtyChange={setDirty}
            onSaved={(created) => {
              updateWorkflow({ storyId: story.id, transcriptVersionId: created.id })
              versionsState.reload()
              navigate(`/stories/${story.id}/review?version=${created.id}`, { replace: true })
            }}
          />
        </section>
      </div>

      <aside className="stack">
        <section className="card card--pad stack">
          <h2 className="card__title">Decision</h2>
          <ReviewStatusLine status={selected.review_status} />
          <p className="muted small">
            The storyteller decides what is true. If that isn’t you, ask them to read this text before
            approving it.
          </p>
          {dirty && (
            <Notice tone="info">Save your corrections first. A review applies to the saved version.</Notice>
          )}
          <ReviewActions version={selected} reviewerId={ownerId} onDone={() => { versionsState.reload(); reviews.reload() }} disabled={dirty} />
        </section>

        <section className="card card--pad stack">
          <h2 className="card__title">Review history</h2>
          {reviews.loading && !reviews.data ? (
            <LoadingState label="Loading…" />
          ) : reviews.error ? (
            <ErrorState error={reviews.error} onRetry={reviews.reload} title="Couldn’t load history" />
          ) : (reviews.data ?? []).length === 0 ? (
            <p className="muted">No reviews of this version yet.</p>
          ) : (
            <ul className="list">
              {(reviews.data ?? []).map((r) => (
                <li key={r.id} className="list__item list__item--col">
                  <div className="row row--wrap">
                    <ReviewBadge status={r.decision} />
                    <span className="muted small">
                      {DECISION_LABEL[r.decision]} · {formatDateTime(r.created_at)} · reviewer {shortId(r.reviewer_id)}
                    </span>
                  </div>
                  {r.comment && <p className="small">{r.comment}</p>}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card card--pad stack">
          <h2 className="card__title">Versions</h2>
          <ul className="list">
            {sameKind.map((v) => (
              <li key={v.id} className="list__item">
                <div className="stack stack--xs">
                  <Link className={`link${v.id === selected.id ? ' link--current' : ''}`} to={`/stories/${story.id}/review?version=${v.id}`}>
                    Version {v.version_number}
                  </Link>
                  <span className="muted small">
                    {formatDateTime(v.created_at)}
                  </span>
                </div>
                <div className="row row--wrap">
                  <OriginBadge origin={v.origin} />
                  <ReviewBadge status={v.review_status} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </div>
  )
}
