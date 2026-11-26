import type { ReactNode } from 'react'
import type {
  ContentOrigin,
  ProcessingJobStatus,
  ReviewStatus,
  StoryQuestionStatus,
  StoryStatus,
} from '../../types'

type Tone = 'neutral' | 'green' | 'gold' | 'clay' | 'blue'

export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge badge--${tone}`}>{children}</span>
}

const REVIEW: Record<ReviewStatus, { tone: Tone; label: string }> = {
  unreviewed: { tone: 'gold', label: 'Awaiting review' },
  approved: { tone: 'green', label: 'Approved' },
  changes_requested: { tone: 'clay', label: 'Needs revision' },
  rejected: { tone: 'neutral', label: 'Rejected' },
}
export function ReviewBadge({ status }: { status: ReviewStatus }) {
  const s = REVIEW[status]
  return <Badge tone={s.tone}>{s.label}</Badge>
}

const STORY: Record<StoryStatus, { tone: Tone; label: string }> = {
  draft: { tone: 'neutral', label: 'Draft' },
  processing: { tone: 'blue', label: 'Processing' },
  in_review: { tone: 'gold', label: 'In review' },
  completed: { tone: 'green', label: 'Completed' },
}
export function StoryStatusBadge({ status }: { status: StoryStatus }) {
  const s = STORY[status]
  return <Badge tone={s.tone}>{s.label}</Badge>
}

const JOB: Record<ProcessingJobStatus, { tone: Tone; label: string }> = {
  queued: { tone: 'neutral', label: 'Waiting' },
  running: { tone: 'blue', label: 'Processing' },
  succeeded: { tone: 'green', label: 'Completed' },
  failed: { tone: 'clay', label: 'Failed' },
  cancelled: { tone: 'neutral', label: 'Cancelled' },
}
export function JobBadge({ status }: { status: ProcessingJobStatus }) {
  const s = JOB[status]
  return <Badge tone={s.tone}>{s.label}</Badge>
}

const ORIGIN: Record<ContentOrigin, string> = {
  ai_generated: 'AI draft',
  human_created: 'Written by a person',
  human_edited: 'Corrected by a person',
}
export function OriginBadge({ origin }: { origin: ContentOrigin }) {
  return <Badge tone={origin === 'ai_generated' ? 'blue' : 'green'}>{ORIGIN[origin]}</Badge>
}

const QUESTION: Record<StoryQuestionStatus, { tone: Tone; label: string }> = {
  suggested: { tone: 'gold', label: 'Suggested' },
  asked: { tone: 'green', label: 'Asked' },
  dismissed: { tone: 'neutral', label: 'Dismissed' },
}
export function QuestionBadge({ status }: { status: StoryQuestionStatus }) {
  const s = QUESTION[status]
  return <Badge tone={s.tone}>{s.label}</Badge>
}
