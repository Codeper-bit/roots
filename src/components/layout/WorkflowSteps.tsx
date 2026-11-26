import { Link } from '../../lib/router'
import { Icon } from '../ui/Icon'

export type StepKey = 'story' | 'participant' | 'consent' | 'record' | 'transcribe' | 'review'

const STEPS: Array<{ key: StepKey; label: string; path: string }> = [
  { key: 'story', label: 'Story', path: '' },
  { key: 'participant', label: 'Storyteller', path: '/participant' },
  { key: 'consent', label: 'Consent', path: '/consent' },
  { key: 'record', label: 'Record', path: '/record' },
  { key: 'transcribe', label: 'Transcribe', path: '/transcribe' },
  { key: 'review', label: 'Review', path: '/review' },
]

export function WorkflowSteps({
  current,
  storyId,
  participantId,
}: {
  current: StepKey
  storyId?: string
  participantId?: string
}) {
  const currentIndex = STEPS.findIndex((s) => s.key === current)
  return (
    <nav aria-label="Story steps" className="steps">
      <ol className="steps__list">
        {STEPS.map((step, i) => {
          const state = i < currentIndex ? 'done' : i === currentIndex ? 'current' : 'todo'
          const linkable = storyId && step.key !== 'story'
          const href = linkable
            ? `/stories/${storyId}${step.path}${participantId && (step.key === 'consent' || step.key === 'record' || step.key === 'transcribe') ? `?participant=${participantId}` : ''}`
            : storyId
              ? `/stories/${storyId}`
              : undefined
          const content = (
            <>
              <span className="steps__marker">{state === 'done' ? <Icon name="check" size={14} /> : i + 1}</span>
              <span className="steps__label">{step.label}</span>
            </>
          )
          return (
            <li key={step.key} className={`steps__item steps__item--${state}`} aria-current={state === 'current' ? 'step' : undefined}>
              {href && state !== 'current' ? <Link to={href}>{content}</Link> : <span>{content}</span>}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
