import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { getAudioAsset } from '../api/audio'
import { listContentVersions } from '../api/content'
import { listStoryProcessingJobs } from '../api/processing'
import { transcribe } from '../api/transcription'
import { StoryScope, type StoryContext } from '../components/layout/StoryScope'
import { AudioPlayer } from '../components/recording/AudioPlayer'
import { TranscriptPane } from '../components/transcription/TranscriptPane'
import { TranslationPanel } from '../components/transcription/TranslationPanel'
import { Badge, JobBadge, OriginBadge, ReviewBadge } from '../components/ui/Badge'
import { Button, ButtonLink } from '../components/ui/Button'
import { Select } from '../components/ui/Field'
import { Icon } from '../components/ui/Icon'
import { EmptyState, ErrorState, LoadingState, Notice } from '../components/ui/States'
import { useToast } from '../components/ui/Toast'
import { useAsync } from '../hooks/useAsync'
import { useConsents } from '../hooks/useConsents'
import { getLocalAudio } from '../lib/localAudio'
import { Link, useParams } from '../lib/router'
import { updateWorkflow, useWorkflow, workflowForStory } from '../lib/workflow'
import type { ContentVersion } from '../types'
import { describeError } from '../utils/errors'
import { formatDateTime } from '../utils/formatDate'
import { formatBytes, formatDuration } from '../utils/formatDuration'
import {
  LANGUAGE_CODE_PATTERN,
  SEEDED_LANGUAGES,
  hasLimitedSpeechRecognition,
  languageName,
} from '../utils/languages'

export function TranscriptionPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="transcribe">
      {(ctx) => <Workspace ctx={ctx} />}
    </StoryScope>
  )
}

type Tab = 'transcript' | 'translation' | 'details'

// A job the server still calls queued/running after this long was almost
// certainly interrupted (server restart, closed tab); don't lock the page on it.
const STALE_JOB_MS = 10 * 60 * 1000

function Workspace({ ctx }: { ctx: StoryContext }) {
  const { story, participant, ownerId } = ctx
  const toast = useToast()
  const workflow = workflowForStory(useWorkflow(), story.id)
  const consents = useConsents(participant?.id)

  const data = useAsync(
    async (signal) => {
      const [versions, jobs] = await Promise.all([
        listContentVersions(story.id, signal),
        listStoryProcessingJobs(story.id, signal),
      ])
      return { versions, jobs }
    },
    [story.id],
  )

  // The API returns jobs newest-first; everything below assumes oldest-first.
  const jobs = useMemo(
    () => [...(data.data?.jobs ?? [])].sort((a, b) => a.created_at.localeCompare(b.created_at)),
    [data.data],
  )

  // Audio: the id saved by the recording step, else the newest transcription job's audio.
  const jobAudioId = useMemo(() => {
    const withAudio = jobs.filter((j) => j.audio_asset_id)
    return withAudio.length ? withAudio[withAudio.length - 1].audio_asset_id : null
  }, [jobs])
  const audioAssetId = workflow.audioAssetId ?? jobAudioId ?? null
  const asset = useAsync(
    async (signal) => (audioAssetId ? getAudioAsset(audioAssetId, signal) : null),
    [audioAssetId],
  )

  const [language, setLanguage] = useState<string>(story.source_language)
  const [customLanguage, setCustomLanguage] = useState('')
  const [useCustom, setUseCustom] = useState(false)
  const [running, setRunning] = useState(false)
  const [runError, setRunError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('transcript')
  const [dirty, setDirty] = useState(false)
  const inFlight = useRef(false)

  const languageCode = useCustom ? customLanguage.trim().toLowerCase() : language
  const versions = data.data?.versions ?? []

  const transcripts = versions.filter((v) => v.content_type === 'transcript')
  const activeLang =
    transcripts.some((v) => v.language_code === story.source_language)
      ? story.source_language
      : ([...transcripts].sort((a, b) => b.created_at.localeCompare(a.created_at))[0]?.language_code ?? story.source_language)
  const latest: ContentVersion | null =
    transcripts.filter((v) => v.language_code === activeLang).sort((a, b) => b.version_number - a.version_number)[0] ?? null

  const transcriptionJobs = jobs.filter((j) => j.job_type === 'transcription')
  const lastJob = transcriptionJobs[transcriptionJobs.length - 1]
  const serverBusy =
    lastJob != null &&
    (lastJob.status === 'queued' || lastJob.status === 'running') &&
    Date.now() - Date.parse(lastJob.updated_at) < STALE_JOB_MS

  // Poll while the server reports a job we did not start in this tab (e.g. after a refresh).
  const reload = data.reload
  useEffect(() => {
    if (!serverBusy || running) return
    const id = window.setInterval(reload, 4000)
    return () => window.clearInterval(id)
  }, [serverBusy, running, reload])

  const transcriptionConsent = consents.data?.byPurpose.transcription.state ?? 'unknown'
  const translationConsent = consents.data?.byPurpose.translation.state ?? 'unknown'
  const consentHref = `/stories/${story.id}/consent${participant ? `?participant=${participant.id}` : ''}`
  const uploaded = asset.data?.upload_status === 'uploaded'

  const blockers: string[] = []
  if (!participant) blockers.push('Add the storyteller first.')
  if (transcriptionConsent !== 'granted' && transcriptionConsent !== 'unknown') blockers.push('The storyteller has not granted permission to transcribe.')
  if (!audioAssetId) blockers.push('There is no recording for this story yet.')
  else if (asset.data && !uploaded) blockers.push(`The recording’s upload status is “${asset.data.upload_status}”.`)
  if (!LANGUAGE_CODE_PATTERN.test(languageCode)) blockers.push('Enter a 2–3 letter language code.')
  const canRun = blockers.length === 0 && !!asset.data && transcriptionConsent === 'granted'

  const start = useCallback(async () => {
    if (inFlight.current || !participant || !audioAssetId) return
    inFlight.current = true
    setRunning(true)
    setRunError(null)
    try {
      const created = await transcribe({
        participant_id: participant.id,
        story_id: story.id,
        audio_asset_id: audioAssetId,
        language_code: languageCode,
        created_by: ownerId,
      })
      updateWorkflow({ storyId: story.id, transcriptVersionId: created.id })
      toast.success('Transcript ready to review.')
    } catch (err) {
      setRunError(describeError(err))
    } finally {
      inFlight.current = false
      setRunning(false)
      reload()
    }
  }, [participant, audioAssetId, story.id, languageCode, ownerId, toast, reload])

  const status: 'waiting' | 'processing' | 'completed' | 'failed' = running || serverBusy
    ? 'processing'
    : runError || (lastJob?.status === 'failed' && !latest)
      ? 'failed'
      : latest
        ? 'completed'
        : 'waiting'
  const STATUS_LABEL = { waiting: 'Waiting to start', processing: 'Processing', completed: 'Completed', failed: 'Failed' } as const

  const local = getLocalAudio(audioAssetId)

  if (data.loading && !data.data) return <LoadingState label="Opening the workspace…" />
  if (data.error && !data.data) return <ErrorState error={data.error} onRetry={data.reload} title="We couldn’t load this story’s transcript" />

  return (
    <div className="workspace">
      <div className="tabs workspace__tabs" role="tablist" aria-label="Workspace sections">
        {(['transcript', 'translation', 'details'] as Tab[]).map((t) => (
          <button
            key={t}
            role="tab"
            type="button"
            aria-selected={tab === t}
            className={`tab${tab === t ? ' tab--active' : ''}${t === 'details' ? ' tab--mobile-only' : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'transcript' ? 'Transcript' : t === 'translation' ? 'Translation' : 'Details'}
          </button>
        ))}
      </div>

      <div className={`workspace__main${tab === 'details' ? ' workspace__main--hide-mobile' : ''}`}>
        <section className="card card--pad stack" aria-label="Original recording">
          <h2 className="card__title">
            <Icon name="fileAudio" size={20} /> Original recording
          </h2>
          {local ? (
            <AudioPlayer src={local.url} durationHintMs={asset.data?.duration_ms} label="Original recording" />
          ) : audioAssetId ? (
            <Notice tone="info" title="Playback isn’t available after a refresh">
              The recording is stored privately. The server can’t hand it back for playback yet; it
              plays here only in the tab where it was recorded or uploaded.
            </Notice>
          ) : (
            <p className="muted">No recording has been saved for this story yet.</p>
          )}
          {asset.data && (
            <p className="muted small">
              {asset.data.mime_type} · {formatBytes(asset.data.size_bytes)}
              {asset.data.duration_ms != null ? ` · ${formatDuration(asset.data.duration_ms)}` : ''} ·{' '}
              {asset.data.upload_status}
            </p>
          )}
        </section>

        <div className="workspace__panel">
          {tab !== 'translation' ? (
            <section className="card card--pad stack" aria-label="Transcript">
              <div className="section-head">
                <h2 className="card__title">Transcript</h2>
                {latest && (
                  <div className="row row--wrap">
                    <OriginBadge origin={latest.origin} />
                    <span className="muted small">v{latest.version_number}</span>
                  </div>
                )}
              </div>
              {status === 'processing' && (
                <Notice tone="info" title="Transcribing…">
                  Listening to the recording and writing it down. This can take a minute for longer
                  recordings. Please keep this page open.
                </Notice>
              )}
              {runError && (
                <Notice tone="error" title="The transcription didn’t finish" action={<Button size="sm" variant="secondary" onClick={start} disabled={!canRun || running}>Try again</Button>}>
                  {runError}
                </Notice>
              )}
              {latest ? (
                <>
                  <Notice tone="warning" title="This is a draft written by AI">
                    It may contain mistakes, especially with names, places and words from your
                    language. Correct anything that’s wrong, then let the storyteller review it.
                  </Notice>
                  <TranscriptPane
                    version={latest}
                    userId={ownerId}
                    onSaved={() => data.reload()}
                    onDirtyChange={setDirty}
                  />
                </>
              ) : (
                status !== 'processing' && (
                  <EmptyState icon="fileAudio" title="No transcript yet">
                    Start a transcription from the panel on the right. Nothing is written until the
                    server confirms it.
                  </EmptyState>
                )
              )}
            </section>
          ) : (
            <section className="card card--pad stack">
              <h2 className="card__title">
                <Icon name="languages" size={20} /> Original and translation
              </h2>
              <TranslationPanel
                storyId={story.id}
                sourceLanguage={activeLang}
                original={latest}
                versions={versions}
                translationConsent={translationConsent}
                consentHref={consentHref}
                userId={ownerId}
                participantId={participant?.id ?? null}
                onSaved={data.reload}
              />
            </section>
          )}
        </div>
      </div>

      <aside className={`workspace__side${tab === 'details' ? ' workspace__side--show' : ''}`} aria-label="Transcription details">
        <section className="card card--pad stack">
          <h2 className="card__title">Details</h2>
          <dl className="facts facts--stack">
            <div>
              <dt>Original language</dt>
              <dd>{languageName(activeLang)}</dd>
            </div>
            <div>
              <dt>Translation</dt>
              <dd>
                {[...new Set(versions.filter((v) => v.content_type === 'translation').map((v) => languageName(v.language_code)))].join(', ') ||
                  'None yet'}
              </dd>
            </div>
            <div>
              <dt>Transcription</dt>
              <dd>
                <Badge tone={status === 'completed' ? 'green' : status === 'failed' ? 'clay' : status === 'processing' ? 'blue' : 'neutral'}>
                  {STATUS_LABEL[status]}
                </Badge>
              </dd>
            </div>
            <div>
              <dt>Review</dt>
              <dd>{latest ? <ReviewBadge status={latest.review_status} /> : <span className="muted">—</span>}</dd>
            </div>
          </dl>
        </section>

        <section className="card card--pad stack">
          <h2 className="card__title">Transcribe</h2>
          {useCustom ? (
            <label className="field">
              <span className="field__label">Spoken language code</span>
              <input
                className="input"
                value={customLanguage}
                maxLength={3}
                onChange={(e) => setCustomLanguage(e.target.value)}
              />
            </label>
          ) : (
            <Select label="Spoken language" value={language} onChange={(e) => setLanguage(e.target.value)} disabled={running}>
              {[...SEEDED_LANGUAGES.map((l) => l.code), ...(SEEDED_LANGUAGES.some((l) => l.code === story.source_language) ? [] : [story.source_language])].map((code) => (
                <option key={code} value={code}>
                  {languageName(code)}
                </option>
              ))}
            </Select>
          )}
          <Button variant="ghost" size="sm" onClick={() => setUseCustom((v) => !v)} disabled={running}>
            {useCustom ? 'Pick from list' : 'Use another language code'}
          </Button>
          {hasLimitedSpeechRecognition(languageCode) && (
            <Notice tone="warning" title={`${languageName(languageCode)} support is limited`}>
              The speech model wasn’t trained on {languageName(languageCode)}, so it has to guess
              what it hears. Expect many mistakes. Treat the result as a rough starting point and
              correct it carefully, or type the transcript yourself.
            </Notice>
          )}
          {blockers.map((b) => (
            <p key={b} className="muted small">
              <Icon name="info" size={14} /> {b}
            </p>
          ))}
          {transcriptionConsent !== 'granted' && transcriptionConsent !== 'unknown' && (
            <Link className="link" to={consentHref}>
              Review consent
            </Link>
          )}
          <Button size="lg" icon="fileAudio" onClick={start} loading={running} disabled={!canRun || running || serverBusy}>
            {latest ? 'Transcribe again' : 'Start transcription'}
          </Button>
          {latest && <p className="muted small">A new AI draft is added as a new version. Earlier versions are kept.</p>}
        </section>

        <section className="card card--pad stack">
          <h2 className="card__title">Next</h2>
          {dirty && <p className="muted small">You have unsaved corrections. Save them before reviewing.</p>}
          <ButtonLink to={`/stories/${story.id}/review`} icon="checkCircle" variant={latest ? 'primary' : 'secondary'}>
            Review the transcript
          </ButtonLink>
          <ButtonLink to={`/stories/${story.id}`} variant="ghost">
            View story
          </ButtonLink>
        </section>

        {transcriptionJobs.length > 0 && (
          <section className="card card--pad stack">
            <h2 className="card__title">Attempts</h2>
            <ul className="list">
              {[...transcriptionJobs].reverse().slice(0, 5).map((j) => (
                <li key={j.id} className="list__item list__item--col">
                  <div className="row">
                    <JobBadge status={j.status} />
                    <span className="muted small">{formatDateTime(j.created_at)}</span>
                  </div>
                  {j.error_message && <p className="small job-error">{j.error_message}</p>}
                </li>
              ))}
            </ul>
          </section>
        )}
      </aside>
    </div>
  )
}
