import { useState } from 'react'
import { createConsent, withdrawConsent } from '../api/consents'
import { StoryScope, type StoryContext } from '../components/layout/StoryScope'
import { Badge } from '../components/ui/Badge'
import { Button, ButtonLink } from '../components/ui/Button'
import { Icon } from '../components/ui/Icon'
import { Modal } from '../components/ui/Modal'
import { EmptyState, ErrorState, LoadingState, Notice } from '../components/ui/States'
import { useToast } from '../components/ui/Toast'
import { useConsents } from '../hooks/useConsents'
import { CONSENT_PURPOSES, type ConsentPurposeInfo, type PurposeConsent } from '../lib/consent'
import { Link, navigate, useParams } from '../lib/router'
import { updateWorkflow } from '../lib/workflow'
import type { ConsentDecision, ConsentPurpose } from '../types'
import { describeError } from '../utils/errors'
import { formatDateTime } from '../utils/formatDate'

export function ConsentPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="consent">
      {(ctx) => <ConsentBody ctx={ctx} />}
    </StoryScope>
  )
}

function ConsentBody({ ctx }: { ctx: StoryContext }) {
  const { story, participant, participants } = ctx
  const toast = useToast()
  const consents = useConsents(participant?.id)
  const [busy, setBusy] = useState<ConsentPurpose | null>(null)
  const [withdrawing, setWithdrawing] = useState<PurposeConsent | null>(null)
  const [withdrawInfo, setWithdrawInfo] = useState<ConsentPurposeInfo | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  if (!participant) {
    return (
      <EmptyState
        icon="users"
        title="Add the storyteller first"
        action={<ButtonLink to={`/stories/${story.id}/participant`}>Add a participant</ButtonLink>}
      >
        Consent belongs to a person, so there must be someone to ask.
      </EmptyState>
    )
  }

  async function decide(purpose: ConsentPurpose, status: ConsentDecision) {
    if (busy || !participant) return
    setBusy(purpose)
    setActionError(null)
    try {
      await createConsent({ participant_id: participant.id, purpose, status })
      toast.success(status === 'granted' ? 'Permission recorded.' : 'Choice recorded: not granted.')
      consents.reload()
    } catch (err) {
      setActionError(describeError(err))
    } finally {
      setBusy(null)
    }
  }

  async function confirmWithdraw() {
    const record = withdrawing?.record
    const info = withdrawInfo
    if (!record || !info || busy) return
    setBusy(info.purpose)
    setActionError(null)
    try {
      await withdrawConsent(record.id)
      toast.success('Permission withdrawn.')
      setWithdrawing(null)
      consents.reload()
    } catch (err) {
      setActionError(describeError(err))
      setWithdrawing(null)
    } finally {
      setBusy(null)
    }
  }

  const by = consents.data?.byPurpose
  const storageGranted = by?.audio_storage.state === 'granted'
  const transcriptionGranted = by?.transcription.state === 'granted'
  const recordHref = `/stories/${story.id}/record?participant=${participant.id}`

  return (
    <div className="stack stack--lg narrow">
      <div className="card card--pad stack">
        <h2 className="card__title">
          <Icon name="shield" size={22} /> Consent for {participant.display_name}
        </h2>
        <p>
          These choices belong to <strong>{participant.display_name}</strong>. Please read each one to
          them in their own language if you need to. Roots records a choice only when a button is
          pressed, and nothing is selected for them. They can say no, and they can change their mind
          later.
        </p>
        {participants.length > 1 && (
          <p className="muted small">
            Acting for:{' '}
            {participants.map((p, i) => (
              <span key={p.id}>
                {i > 0 && ' · '}
                {p.id === participant.id ? (
                  <strong>{p.display_name}</strong>
                ) : (
                  <Link className="link" to={`/stories/${story.id}/consent?participant=${p.id}`}>
                    {p.display_name}
                  </Link>
                )}
              </span>
            ))}
          </p>
        )}
      </div>

      {actionError && (
        <Notice tone="error" title="That choice wasn’t saved">
          {actionError}
        </Notice>
      )}

      {consents.loading && !consents.data ? (
        <LoadingState label="Checking recorded permissions…" />
      ) : consents.error && !consents.data ? (
        <ErrorState error={consents.error} title="We couldn’t check consent" onRetry={consents.reload} />
      ) : (
        <ul className="consent-list">
          {CONSENT_PURPOSES.map((info) => {
            const c = by![info.purpose]
            const isBusy = busy === info.purpose
            return (
              <li key={info.purpose} className={`consent consent--${c.state}`}>
                <div className="consent__main">
                  <h3 className="consent__title">
                    {info.title}
                    <Badge tone={info.required ? 'gold' : 'neutral'}>{info.required ? 'Needed to continue' : 'Optional'}</Badge>
                  </h3>
                  <p>{info.description}</p>
                  <p className="consent__status" aria-live="polite">
                    {c.state === 'granted' && (
                      <>
                        <Badge tone="green">Granted</Badge>{' '}
                        <span className="muted small">{formatDateTime(c.record?.granted_at)}</span>
                      </>
                    )}
                    {c.state === 'declined' && <Badge tone="clay">Declined</Badge>}
                    {c.state === 'withdrawn' && (
                      <>
                        <Badge tone="clay">Withdrawn</Badge>{' '}
                        <span className="muted small">{formatDateTime(c.record?.withdrawn_at)}</span>
                      </>
                    )}
                    {c.state === 'none' && <Badge>Not answered yet</Badge>}
                  </p>
                </div>
                <div className="consent__actions">
                  {c.state === 'granted' ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={busy !== null}
                      onClick={() => {
                        setWithdrawInfo(info)
                        setWithdrawing(c)
                      }}
                    >
                      Withdraw
                    </Button>
                  ) : (
                    <>
                      <Button size="sm" icon="check" loading={isBusy} disabled={busy !== null} onClick={() => decide(info.purpose, 'granted')}>
                        I agree
                      </Button>
                      {c.state !== 'declined' && (
                        <Button size="sm" variant="secondary" disabled={busy !== null} onClick={() => decide(info.purpose, 'declined')}>
                          I do not agree
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}

      <div className="card card--pad stack">
        {!storageGranted && by && (
          <Notice tone="warning" title="Recording is locked">
            Audio can’t be recorded or uploaded until “Keep my recording” is granted.
          </Notice>
        )}
        {storageGranted && !transcriptionGranted && (
          <Notice tone="info" title="Transcription is locked">
            You can record now, but a written draft can’t be made until “Write down what I say” is
            granted.
          </Notice>
        )}
        <div>
          <Button
            size="lg"
            iconRight="arrowRight"
            disabled={!storageGranted}
            onClick={() => {
              updateWorkflow({ storyId: story.id, participantId: participant.id })
              navigate(recordHref)
            }}
          >
            Continue to recording
          </Button>
        </div>
      </div>

      <Modal
        open={withdrawing !== null}
        title="Withdraw permission?"
        onClose={() => setWithdrawing(null)}
        footer={
          <>
            <Button variant="ghost" onClick={() => setWithdrawing(null)}>
              Keep it
            </Button>
            <Button variant="danger" loading={busy !== null} onClick={confirmWithdraw}>
              Withdraw
            </Button>
          </>
        }
      >
        <p>
          {participant.display_name} will no longer have given permission for “{withdrawInfo?.title}”.
          Anything that needs it will stop working until they agree again.
        </p>
      </Modal>
    </div>
  )
}
