import { useMemo, useState } from 'react'
import { RequireIdentity } from '../components/layout/RequireIdentity'
import { ReviewCard } from '../components/review/ReviewCard'
import { DashboardStats } from '../components/dashboard/DashboardStats'
import { PageHeader } from '../components/ui/PageHeader'
import { EmptyState, ErrorState, LoadingState, Notice } from '../components/ui/States'
import { latestVersions, useStoriesContent } from '../hooks/useStoryContent'
import { useStories } from '../hooks/useStories'
import type { ContentVersion, ReviewStatus, Story } from '../types'

type Filter = ReviewStatus

const TABS: Array<{ key: Filter; label: string }> = [
  { key: 'unreviewed', label: 'Pending review' },
  { key: 'approved', label: 'Approved' },
  { key: 'changes_requested', label: 'Needs revision' },
  { key: 'rejected', label: 'Rejected' },
]

export function ReviewsPage() {
  return (
    <div className="stack stack--lg">
      <PageHeader
        eyebrow="Review"
        title="Content review"
        description="Every transcript and translation waits here until a person confirms it. The storyteller has the final word."
      />
      <RequireIdentity>{(ownerId) => <ReviewsBody ownerId={ownerId} />}</RequireIdentity>
    </div>
  )
}

function ReviewsBody({ ownerId }: { ownerId: string }) {
  const stories = useStories(ownerId)
  const content = useStoriesContent(stories.data?.stories ?? null)
  const [filter, setFilter] = useState<Filter>('unreviewed')

  const rows = useMemo(() => {
    const out: Array<{ story: Story; version: ContentVersion }> = []
    for (const item of content.data?.items ?? []) {
      for (const version of latestVersions(item.versions)) out.push({ story: item.story, version })
    }
    return out.sort((a, b) => b.version.created_at.localeCompare(a.version.created_at))
  }, [content.data])

  const counts = useMemo(() => {
    const c: Record<ReviewStatus, number> = { unreviewed: 0, approved: 0, changes_requested: 0, rejected: 0 }
    for (const r of rows) c[r.version.review_status]++
    return c
  }, [rows])

  if ((stories.loading && !stories.data) || (content.loading && !content.data)) return <LoadingState label="Collecting content to review…" />
  if (stories.error && !stories.data) return <ErrorState error={stories.error} onRetry={stories.reload} title="We couldn’t load your stories" />
  if (content.error && !content.data) return <ErrorState error={content.error} onRetry={content.reload} title="We couldn’t load content" />

  const visible = rows.filter((r) => r.version.review_status === filter)

  return (
    <>
      <DashboardStats
        stats={TABS.map((t) => ({ label: t.label, value: counts[t.key] }))}
      />
      {content.data?.truncated && <Notice tone="info">Showing your 40 most recent stories.</Notice>}
      <p className="muted small">Only the latest version of each transcript or translation is listed.</p>

      <div className="tabs" role="tablist" aria-label="Review status">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={filter === t.key}
            className={`tab${filter === t.key ? ' tab--active' : ''}`}
            onClick={() => setFilter(t.key)}
          >
            {t.label} <span className="tab__count">{counts[t.key]}</span>
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState icon="checkCircle" title="Nothing here">
          {filter === 'unreviewed' ? 'No content is waiting for review.' : 'No content has this status.'}
        </EmptyState>
      ) : (
        <div className="stack">
          {visible.map(({ story, version }) => (
            <ReviewCard key={version.id} story={story} version={version} reviewerId={ownerId} onDone={content.reload} />
          ))}
        </div>
      )}
    </>
  )
}
