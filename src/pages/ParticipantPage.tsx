import { useState, type FormEvent } from 'react'
import { createParticipant } from '../api/participants'
import { ApiError } from '../api/client'
import { StoryScope, type StoryContext } from '../components/layout/StoryScope'
import { Button } from '../components/ui/Button'
import { Input, Select } from '../components/ui/Field'
import { Badge } from '../components/ui/Badge'
import { Notice } from '../components/ui/States'
import { useToast } from '../components/ui/Toast'
import { navigate, useParams } from '../lib/router'
import { updateWorkflow } from '../lib/workflow'
import type { ParticipantRole } from '../types'
import { describeError } from '../utils/errors'

const ROLES: Array<{ value: ParticipantRole; label: string }> = [
  { value: 'storyteller', label: 'Storyteller — the person telling the story' },
  { value: 'interviewer', label: 'Interviewer — asking the questions' },
  { value: 'family_member', label: 'Family member' },
  { value: 'translator', label: 'Translator' },
  { value: 'reviewer', label: 'Reviewer' },
  { value: 'other', label: 'Other' },
]

const ROLE_LABEL = Object.fromEntries(ROLES.map((r) => [r.value, r.label.split(' — ')[0]])) as Record<ParticipantRole, string>

export function ParticipantPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="participant">
      {(ctx) => <ParticipantBody ctx={ctx} />}
    </StoryScope>
  )
}

function ParticipantBody({ ctx }: { ctx: StoryContext }) {
  const toast = useToast()
  const { story, participants } = ctx
  const [name, setName] = useState('')
  const [role, setRole] = useState<ParticipantRole>('storyteller')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function goToConsent(participantId: string) {
    updateWorkflow({ storyId: story.id, participantId })
    navigate(`/stories/${story.id}/consent?participant=${participantId}`)
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (submitting) return
    const next: Record<string, string> = {}
    if (!name.trim()) next.display_name = 'Enter the person’s name.'
    else if (name.trim().length > 100) next.display_name = 'Keep the name under 100 characters.'
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length) return

    setSubmitting(true)
    try {
      const participant = await createParticipant({ story_id: story.id, display_name: name.trim(), role })
      toast.success(`${participant.display_name} added.`)
      goToConsent(participant.id)
    } catch (err) {
      if (err instanceof ApiError && Object.keys(err.fieldErrors).length) setErrors(err.fieldErrors)
      setFormError(describeError(err))
      setSubmitting(false)
    }
  }

  return (
    <div className="stack stack--lg narrow">
      {participants.length > 0 && (
        <section className="card card--pad stack" aria-labelledby="existing">
          <h2 id="existing" className="card__title">
            Already in this story
          </h2>
          <ul className="list">
            {participants.map((p) => (
              <li key={p.id} className="list__item">
                <div>
                  <strong>{p.display_name}</strong> <Badge>{ROLE_LABEL[p.role]}</Badge>
                </div>
                <Button size="sm" variant="secondary" iconRight="arrowRight" onClick={() => goToConsent(p.id)}>
                  Continue to consent
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <form className="card card--pad stack" onSubmit={submit} noValidate>
        <div>
          <h2 className="card__title">{participants.length ? 'Add another person' : 'Who is telling this story?'}</h2>
          <p className="muted">
            Adding someone does not give Roots any permission. Consent comes next, and only they can
            give it.
          </p>
        </div>
        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.display_name}
          maxLength={100}
          placeholder="Grandmother Adunni"
          required
        />
        <Select label="Their role" value={role} onChange={(e) => setRole(e.target.value as ParticipantRole)} error={errors.role}>
          {ROLES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </Select>
        {formError && (
          <Notice tone="error" title="They couldn’t be added">
            {formError}
          </Notice>
        )}
        <div>
          <Button type="submit" size="lg" iconRight="arrowRight" loading={submitting}>
            Add and continue
          </Button>
        </div>
      </form>
    </div>
  )
}
