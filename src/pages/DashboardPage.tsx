import { useMemo } from 'react'
import { DashboardStats } from '../components/dashboard/DashboardStats'
import { RecentStories } from '../components/dashboard/RecentStories'
import { RequireIdentity } from '../components/layout/RequireIdentity'
import { ButtonLink } from '../components/ui/Button'
import { Icon } from '../components/ui/Icon'
import { PageHeader } from '../components/ui/PageHeader'
import { EmptyState, ErrorState, LoadingState, Notice } from '../components/ui/States'
import { latestVersions, useStoriesContent } from '../hooks/useStoryContent'
import { useStories } from '../hooks/useStories'
import { useWorkflow } from '../lib/workflow'
import type { ReviewStatus } from '../types'

export function DashboardPage() {
  return (
    <div className="stack stack--lg">
      <PageHeader
        eyebrow="Your archive"
        title="Welcome back"
        description="Every story here began with someone’s voice. Pick one up where you left off, or record a new one."
        actions={
          <ButtonLink to="/stories/new" icon="mic" size="lg">
            Record a Story
          </ButtonLink>
        }
      />
      <RequireIdentity>{(ownerId) => <DashboardBody ownerId={ownerId} />}</RequireIdentity>
    </div>
  )
}

function DashboardBody({ ownerId }: { ownerId: string }) {
  const stories = useStories(ownerId)
  const content = useStoriesContent(stories.data?.stories ?? null)
  const workflow = useWorkflow()

  const reviewByStory = useMemo(() => {
    const map = new Map<string, ReviewStatus | null>()
    for (const item of content.data?.items ?? []) {
      const transcripts = latestVersions(item.versions).filter((v) => v.content_type === 'transcript')
      const preferred = transcripts.find((t) => t.language_code === item.story.source_language) ?? transcripts[0]
      map.set(item.story.id, preferred ? preferred.review_status : null)
    }
    return map
  }, [content.data])

  if (stories.loading && !stories.data) return <LoadingState label="Gathering your stories…" />
  if (stories.error || !stories.data) {
    return <ErrorState error={stories.error} title="We couldn’t load your stories" onRetry={stories.reload} />
  }

  const list = stories.data.stories
  const reviewKnown = !!content.data
  const awaiting = reviewKnown ? [...reviewByStory.values()].filter((s) => s === 'unreviewed').length : null
  const approved = reviewKnown ? [...reviewByStory.values()].filter((s) => s === 'approved').length : null
  const resumeId = workflow.storyId && list.some((s) => s.id === workflow.storyId) ? workflow.storyId : null

  return (
    <>
      <DashboardStats
        stats={[
          { label: 'Stories', value: stories.data.total },
          { label: 'Transcripts awaiting review', value: awaiting },
          { label: 'Transcripts approved', value: approved },
        ]}
      />

      {content.data?.truncated && (
        <Notice tone="info">Review counts cover your 40 most recent stories.</Notice>
      )}
      {content.error != null && !content.data && (
        <Notice tone="warning" title="Review status unavailable">
          We couldn’t load transcript review status just now. Your stories are shown without it.
        </Notice>
      )}

      <section className="stack" aria-labelledby="recent-title">
        <div className="section-head">
          <h2 id="recent-title" className="section-title">
            Recent stories
          </h2>
          <div className="row row--wrap">
            {resumeId && (
              <ButtonLink to={`/stories/${resumeId}`} variant="secondary" size="sm" iconRight="arrowRight">
                Continue last story
              </ButtonLink>
            )}
            <ButtonLink to="/reviews" variant="ghost" size="sm" icon="checkCircle">
              Review queue
            </ButtonLink>
          </div>
        </div>
        {list.length === 0 ? (
          <EmptyState
            icon="mic"
            title="No stories yet"
            action={
              <ButtonLink to="/stories/new" icon="mic">
                Record your first story
              </ButtonLink>
            }
          >
            Start with the story of someone you want to remember.
          </EmptyState>
        ) : (
          <RecentStories stories={list.slice(0, 9)} reviewByStory={reviewByStory} />
        )}
      </section>

      <section className="card card--pad" aria-labelledby="rec-title">
        <h2 id="rec-title" className="card__title">
          <Icon name="fileAudio" size={20} /> Recent recordings
        </h2>
        <p className="muted">
          A list of recordings isn’t available yet because the server can’t list audio files. Open a
          story to see its recording and transcript.
        </p>
      </section>
    </>
  )
}
