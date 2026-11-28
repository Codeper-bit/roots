import { useMemo } from 'react'
import { getAudioAsset } from '../api/audio'
import { listContentVersions } from '../api/content'
import { listStoryProcessingJobs } from '../api/processing'
import { StoryScope, type StoryContext } from '../components/layout/StoryScope'
import { AudioPlayer } from '../components/recording/AudioPlayer'
import { ShareStory } from '../components/story/ShareStory'
import { StoryQuestions } from '../components/story/StoryQuestions'
import { TranslationPanel } from '../components/transcription/TranslationPanel'
import { Badge, JobBadge, OriginBadge, ReviewBadge, StoryStatusBadge } from '../components/ui/Badge'
import { ButtonLink } from '../components/ui/Button'
import { Icon } from '../components/ui/Icon'
import { ErrorState, LoadingState, Notice } from '../components/ui/States'
import { useAsync } from '../hooks/useAsync'
import { useConsents } from '../hooks/useConsents'
import { getLocalAudio } from '../lib/localAudio'
import { useParams } from '../lib/router'
import { useWorkflow, workflowForStory } from '../lib/workflow'
import type { AudioAsset, ContentVersion } from '../types'
import { formatDate, formatDateTime } from '../utils/formatDate'
import { formatBytes, formatDuration } from '../utils/formatDuration'
import { languageName } from '../utils/languages'

export function StoryDetailPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="story">
      {(ctx) => <Detail ctx={ctx} />}
    </StoryScope>
  )
}

const ROLE = {
  storyteller: 'Storyteller',
  interviewer: 'Interviewer',
  family_member: 'Family member',
  translator: 'Translator',
  reviewer: 'Reviewer',
  other: 'Other',
} as const

function Detail({ ctx }: { ctx: StoryContext }) {
  const { story, participants, participant, ownerId } = ctx
  const workflow = workflowForStory(useWorkflow(), story.id)
  const consents = useConsents(participant?.id)

  const data = useAsync(
    async (signal) => {
      const [versions, jobs] = await Promise.all([
        listContentVersions(story.id, signal),
        listStoryProcessingJobs(story.id, signal),
      ])
      const ids = [...new Set([workflow.audioAssetId, ...jobs.map((j) => j.audio_asset_id)].filter((x): x is string => !!x))]
      const assets = (
        await Promise.all(ids.map((id) => getAudioAsset(id, signal).catch(() => null)))
      ).filter((a): a is AudioAsset => a !== null)
      return { versions, jobs, assets }
    },
    [story.id, workflow.audioAssetId],
  )

  const versions = data.data?.versions ?? []
  const transcript: ContentVersion | null = useMemo(() => {
    const t = versions.filter((v) => v.content_type === 'transcript')
    const pool = t.filter((v) => v.language_code === story.source_language)
    return (pool.length ? pool : t).sort((a, b) => b.version_number - a.version_number || b.created_at.localeCompare(a.created_at))[0] ?? null
  }, [versions, story.source_language])

  const hasAudio = (data.data?.assets.length ?? 0) > 0
  const storage = consents.data?.byPurpose.audio_storage.state
  const pid = participant ? `?participant=${participant.id}` : ''

  let next: { label: string; to: string; why: string } | null = null
  if (data.data) {
    if (participants.length === 0) next = { label: 'Add the storyteller', to: `/stories/${story.id}/participant`, why: 'Every story needs a person who tells it.' }
    else if (consents.data && storage !== 'granted') next = { label: 'Record consent', to: `/stories/${story.id}/consent${pid}`, why: 'Recording is locked until the storyteller gives permission.' }
    else if (!transcript && !hasAudio) next = { label: 'Record or upload audio', to: `/stories/${story.id}/record${pid}`, why: 'No recording has been saved yet.' }
    else if (!transcript) next = { label: 'Transcribe the recording', to: `/stories/${story.id}/transcribe${pid}`, why: 'The recording has no written draft yet.' }
    else if (transcript.review_status === 'unreviewed' || transcript.review_status === 'changes_requested')
      next = { label: 'Review the transcript', to: `/stories/${story.id}/review`, why: transcript.review_status === 'unreviewed' ? 'The draft hasn’t been confirmed by a person.' : 'Corrections were requested.' }
  }

  return (
    <div className="stack stack--lg">
      <section className="card card--pad stack">
        <div className="section-head">
          <div className="row row--wrap">
            <StoryStatusBadge status={story.status} />
            <Badge>{story.visibility === 'family' ? 'Family' : 'Private'}</Badge>
            <Badge>Told in {languageName(story.source_language)}</Badge>
          </div>
          <div className="row row--wrap">
            <span className="muted small">Created {formatDate(story.created_at)}</span>
            <ShareStory
              story={story}
              versions={versions}
              storyteller={(participants.find((p) => p.role === 'storyteller') ?? participant)?.display_name ?? null}
              sharingConsent={consents.data?.byPurpose.family_sharing.state ?? 'unknown'}
              consentHref={`/stories/${story.id}/consent${pid}`}
              reviewHref={`/stories/${story.id}/review`}
            />
          </div>
        </div>
        {story.description ? <p className="story-desc">{story.description}</p> : <p className="muted">No description.</p>}
        <div>
          <h3 className="eyebrow">People</h3>
          {participants.length === 0 ? (
            <p className="muted">No participants yet.</p>
          ) : (
            <ul className="chips">
              {participants.map((p) => (
                <li key={p.id} className="chip">
                  <Icon name="user" size={14} /> {p.display_name} <span className="muted small">· {ROLE[p.role]}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {data.loading && !data.data ? (
        <LoadingState label="Loading the story…" />
      ) : data.error && !data.data ? (
        <ErrorState error={data.error} onRetry={data.reload} title="We couldn’t load this story’s content" />
      ) : (
        data.data && (
          <>
            {next && (
              <section className="card card--pad next-step">
                <div>
                  <p className="eyebrow">Next step</p>
                  <h2 className="card__title">{next.label}</h2>
                  <p className="muted">{next.why}</p>
                </div>
                <ButtonLink to={next.to} iconRight="arrowRight" size="lg">
                  {next.label}
                </ButtonLink>
              </section>
            )}

            <section className="card card--pad stack" aria-labelledby="audio-h">
              <h2 id="audio-h" className="card__title">
                <Icon name="fileAudio" size={20} /> Original recording
              </h2>
              {data.data.assets.length === 0 ? (
                <p className="muted">No recording has been saved for this story.</p>
              ) : (
                <ul className="stack">
                  {data.data.assets.map((a) => {
                    const local = getLocalAudio(a.id)
                    return (
                      <li key={a.id} className="stack stack--sm">
                        <p className="muted small">
                          {a.mime_type} · {formatBytes(a.size_bytes)}
                          {a.duration_ms != null ? ` · ${formatDuration(a.duration_ms)}` : ''} · {formatDateTime(a.created_at)} ·{' '}
                          <Badge tone={a.upload_status === 'uploaded' ? 'green' : a.upload_status === 'failed' ? 'clay' : 'neutral'}>{a.upload_status}</Badge>
                        </p>
                        {local && <AudioPlayer src={local.url} durationHintMs={a.duration_ms} label="Original recording" />}
                      </li>
                    )
                  })}
                </ul>
              )}
              {data.data.assets.length > 0 && !data.data.assets.some((a) => getLocalAudio(a.id)) && (
                <Notice tone="info" title="Playback isn’t available here yet">
                  Recordings are private. The server has no download or signed-link endpoint yet, so
                  audio can only be played in the tab where it was recorded or uploaded.
                </Notice>
              )}
            </section>

            <section className="card card--pad stack" aria-labelledby="tr-h">
              <div className="section-head">
                <h2 id="tr-h" className="card__title">
                  Transcript
                </h2>
                {transcript && (
                  <div className="row row--wrap">
                    <OriginBadge origin={transcript.origin} />
                    <ReviewBadge status={transcript.review_status} />
                  </div>
                )}
              </div>
              {transcript ? (
                <>
                  <p className="reading" lang={transcript.language_code}>
                    {transcript.content}
                  </p>
                  <p className="muted small">
                    Version {transcript.version_number} · {formatDateTime(transcript.created_at)}
                  </p>
                  <div className="row row--wrap">
                    <ButtonLink to={`/stories/${story.id}/review`} variant="secondary" icon="edit">
                      Review or correct
                    </ButtonLink>
                    <ButtonLink to={`/stories/${story.id}/transcribe${pid}`} variant="ghost">
                      Open workspace
                    </ButtonLink>
                  </div>
                </>
              ) : (
                <p className="muted">No transcript yet.</p>
              )}
            </section>

            {transcript && (
              <section className="card card--pad stack" aria-labelledby="tl-h">
                <h2 id="tl-h" className="card__title">
                  <Icon name="languages" size={20} /> Translation
                </h2>
                <TranslationPanel
                  storyId={story.id}
                  sourceLanguage={transcript.language_code}
                  original={transcript}
                  versions={versions}
                  translationConsent={consents.data?.byPurpose.translation.state ?? 'unknown'}
                  consentHref={`/stories/${story.id}/consent${pid}`}
                  userId={ownerId}
                  participantId={participant?.id ?? null}
                  onSaved={data.reload}
                />
              </section>
            )}

            <section className="stack" aria-labelledby="q-h">
              <h2 id="q-h" className="section-title">
                Follow-up questions
              </h2>
              <StoryQuestions storyId={story.id} />
            </section>

            {data.data.jobs.length > 0 && (
              <section className="card card--pad stack" aria-labelledby="jobs-h">
                <h2 id="jobs-h" className="card__title">
                  <Icon name="history" size={20} /> Processing history
                </h2>
                <ul className="list">
                  {[...data.data.jobs].reverse().slice(0, 8).map((j) => (
                    <li key={j.id} className="list__item list__item--col">
                      <div className="row row--wrap">
                        <JobBadge status={j.status} />
                        <span className="small">{j.job_type.replace('_', ' ')}</span>
                        <span className="muted small">{formatDateTime(j.created_at)}</span>
                      </div>
                      {j.error_message && <p className="small job-error">{j.error_message}</p>}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )
      )}
    </div>
  )
}
