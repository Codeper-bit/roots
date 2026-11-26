import { useEffect, type ReactNode } from 'react'
import { listParticipants } from '../../api/participants'
import { getStory } from '../../api/stories'
import { useAsync } from '../../hooks/useAsync'
import { Link, useSearchParams } from '../../lib/router'
import { updateWorkflow, useWorkflow, workflowForStory } from '../../lib/workflow'
import type { Participant, Story } from '../../types'
import { languageName } from '../../utils/languages'
import { ButtonLink } from '../ui/Button'
import { Icon } from '../ui/Icon'
import { ErrorState, LoadingState } from '../ui/States'
import { RequireIdentity } from './RequireIdentity'
import { WorkflowSteps, type StepKey } from './WorkflowSteps'

export interface StoryContext {
  ownerId: string
  story: Story
  participants: Participant[]
  /** The participant this page is acting for (null when the story has none yet). */
  participant: Participant | null
  reload: () => void
}

function pickParticipant(
  participants: Participant[],
  wantedIds: Array<string | undefined | null>,
): Participant | null {
  for (const id of wantedIds) {
    const found = id ? participants.find((p) => p.id === id) : undefined
    if (found) return found
  }
  return participants.find((p) => p.role === 'storyteller') ?? participants[0] ?? null
}

/**
 * Loads a story and its participants, resolves which participant the workflow
 * is acting for (URL ?participant= → saved workflow → storyteller → first) and
 * shows the shared story header + step indicator.
 */
export function StoryScope({
  storyId,
  step,
  children,
}: {
  storyId: string
  step?: StepKey
  children: (ctx: StoryContext) => ReactNode
}) {
  return (
    <RequireIdentity>
      {(ownerId) => (
        <StoryScopeInner ownerId={ownerId} storyId={storyId} step={step}>
          {children}
        </StoryScopeInner>
      )}
    </RequireIdentity>
  )
}

function StoryScopeInner({
  ownerId,
  storyId,
  step,
  children,
}: {
  ownerId: string
  storyId: string
  step?: StepKey
  children: (ctx: StoryContext) => ReactNode
}) {
  const search = useSearchParams()
  const workflow = workflowForStory(useWorkflow(), storyId)
  const state = useAsync(
    async (signal) => {
      const [story, participants] = await Promise.all([
        getStory(storyId, ownerId, signal),
        listParticipants(storyId, signal),
      ])
      return { story, participants }
    },
    [storyId, ownerId],
  )

  const participant = state.data
    ? pickParticipant(state.data.participants, [search.get('participant'), workflow.participantId])
    : null

  const participantId = participant?.id
  useEffect(() => {
    if (state.data) updateWorkflow({ storyId, ...(participantId ? { participantId } : {}) })
  }, [state.data, storyId, participantId])

  if (state.loading && !state.data) return <LoadingState label="Opening story…" />
  if (state.error || !state.data) {
    return (
      <ErrorState
        error={state.error}
        title="We couldn't open this story"
        onRetry={state.reload}
      />
    )
  }

  const { story, participants } = state.data
  return (
    <div className="stack stack--lg">
      <div className="story-bar">
        <div className="story-bar__info">
          <Link to="/dashboard" className="story-bar__back">
            <Icon name="arrowLeft" size={16} /> All stories
          </Link>
          <h1 className="story-bar__title">{story.title}</h1>
          <p className="muted">
            Told in {languageName(story.source_language)}
            {participant ? ` · ${participant.display_name}` : ''}
          </p>
        </div>
        {step !== 'story' && (
          <ButtonLink to={`/stories/${story.id}`} variant="ghost" size="sm">
            Story page
          </ButtonLink>
        )}
      </div>
      {step && step !== 'story' && (
        <WorkflowSteps current={step} storyId={story.id} participantId={participant?.id} />
      )}
      {children({ ownerId, story, participants, participant, reload: state.reload })}
    </div>
  )
}
