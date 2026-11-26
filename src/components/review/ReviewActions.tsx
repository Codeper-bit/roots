import { useState } from 'react'
import { createReview } from '../../api/reviews'
import { describeError } from '../../utils/errors'
import type { ContentVersion, ReviewDecision } from '../../types'
import { Button } from '../ui/Button'
import { Textarea } from '../ui/Field'
import { Modal } from '../ui/Modal'
import { Notice } from '../ui/States'
import { useToast } from '../ui/Toast'

const COPY: Record<ReviewDecision, { title: string; confirm: string; blurb: string; noteRequired: boolean; done: string }> = {
  approved: {
    title: 'Approve this text?',
    confirm: 'Approve',
    blurb: 'You are confirming that this text is an accurate record of the story.',
    noteRequired: false,
    done: 'Approved.',
  },
  changes_requested: {
    title: 'Ask for corrections',
    confirm: 'Request changes',
    blurb: 'Say what needs fixing so it can be corrected and reviewed again.',
    noteRequired: true,
    done: 'Corrections requested.',
  },
  rejected: {
    title: 'Reject this text?',
    confirm: 'Reject',
    blurb: 'Use this when the text should not be kept as the record of the story.',
    noteRequired: false,
    done: 'Rejected.',
  },
}

/** Approve / request changes / reject, recorded through POST /content-reviews. */
export function ReviewActions({
  version,
  reviewerId,
  onDone,
  compact = false,
  disabled = false,
}: {
  version: ContentVersion
  reviewerId: string
  onDone: () => void
  compact?: boolean
  disabled?: boolean
}) {
  const toast = useToast()
  const [decision, setDecision] = useState<ReviewDecision | null>(null)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const copy = decision ? COPY[decision] : null

  function close() {
    if (submitting) return
    setDecision(null)
    setComment('')
    setError(null)
  }

  async function submit() {
    if (!decision || !copy || submitting) return
    if (copy.noteRequired && !comment.trim()) {
      setError('Please add a short note so the person correcting it knows what to fix.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await createReview({
        content_version_id: version.id,
        reviewer_id: reviewerId,
        decision,
        comment: comment.trim() ? comment.trim() : null,
      })
      toast.success(copy.done)
      setDecision(null)
      setComment('')
      onDone()
    } catch (err) {
      setError(describeError(err))
    } finally {
      setSubmitting(false)
    }
  }

  const size = compact ? 'sm' : 'md'
  return (
    <>
      <div className="row row--wrap">
        <Button size={size} icon="check" onClick={() => setDecision('approved')} disabled={disabled}>
          Approve
        </Button>
        <Button size={size} variant="gold" icon="edit" onClick={() => setDecision('changes_requested')} disabled={disabled}>
          Request changes
        </Button>
        <Button size={size} variant="ghost" onClick={() => setDecision('rejected')} disabled={disabled}>
          Reject
        </Button>
      </div>
      <Modal
        open={decision !== null}
        title={copy?.title ?? ''}
        onClose={close}
        footer={
          <>
            <Button variant="ghost" onClick={close} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={submit} loading={submitting}>
              {copy?.confirm}
            </Button>
          </>
        }
      >
        <div className="stack">
          <p>{copy?.blurb}</p>
          <p className="muted small">
            Version {version.version_number} · {version.content_type} · {version.language_code}
          </p>
          <Textarea
            label={copy?.noteRequired ? 'Note' : 'Note (optional)'}
            value={comment}
            maxLength={5000}
            rows={4}
            onChange={(e) => setComment(e.target.value)}
            required={copy?.noteRequired}
          />
          {error && (
            <Notice tone="error" title="Couldn’t save the review">
              {error}
            </Notice>
          )}
        </div>
      </Modal>
    </>
  )
}
