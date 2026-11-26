import { useCallback, useState } from 'react'
import { uploadAudio } from '../api/audio'
import { StoryScope, type StoryContext } from '../components/layout/StoryScope'
import { AudioRecorder, type CapturedAudio } from '../components/recording/AudioRecorder'
import { AudioUploader } from '../components/recording/AudioUploader'
import { Badge } from '../components/ui/Badge'
import { Button, ButtonLink } from '../components/ui/Button'
import { Icon } from '../components/ui/Icon'
import { ErrorState, LoadingState, Notice } from '../components/ui/States'
import { useToast } from '../components/ui/Toast'
import { useConsents } from '../hooks/useConsents'
import { rememberLocalAudio } from '../lib/localAudio'
import { navigate, useParams } from '../lib/router'
import { updateWorkflow } from '../lib/workflow'
import type { AudioAsset } from '../types'
import { describeError } from '../utils/errors'
import { formatBytes, formatDuration } from '../utils/formatDuration'
import { shortId } from '../utils/uuid'

export function RecordingPage() {
  const { storyId } = useParams()
  return (
    <StoryScope storyId={storyId} step="record">
      {(ctx) => <RecordingBody ctx={ctx} />}
    </StoryScope>
  )
}

type Mode = 'record' | 'upload'
type UploadState = 'idle' | 'uploading' | 'uploaded' | 'failed'

function RecordingBody({ ctx }: { ctx: StoryContext }) {
  const { story, participant } = ctx
  const toast = useToast()
  const consents = useConsents(participant?.id)
  const [mode, setMode] = useState<Mode>('record')
  const [recorded, setRecorded] = useState<CapturedAudio | null>(null)
  const [picked, setPicked] = useState<(CapturedAudio & { durationKnown: boolean }) | null>(null)
  const [uploadState, setUploadState] = useState<UploadState>('idle')
  const [progress, setProgress] = useState(0)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [asset, setAsset] = useState<AudioAsset | null>(null)

  const onRecorded = useCallback((audio: CapturedAudio | null) => {
    setRecorded(audio)
    setUploadState('idle')
    setUploadError(null)
    setAsset(null)
  }, [])
  const onPicked = useCallback((audio: (CapturedAudio & { durationKnown: boolean }) | null) => {
    setPicked(audio)
    setUploadState('idle')
    setUploadError(null)
    setAsset(null)
  }, [])

  if (!participant) {
    return (
      <Notice tone="warning" title="Add the storyteller first" action={<ButtonLink to={`/stories/${story.id}/participant`} size="sm">Add a participant</ButtonLink>}>
        Audio is saved on behalf of a participant who has given consent.
      </Notice>
    )
  }
  if (consents.loading && !consents.data) return <LoadingState label="Checking consent…" />
  if (consents.error && !consents.data) return <ErrorState error={consents.error} title="We couldn’t check consent" onRetry={consents.reload} />

  const storage = consents.data?.byPurpose.audio_storage
  const transcription = consents.data?.byPurpose.transcription
  const consentHref = `/stories/${story.id}/consent?participant=${participant.id}`

  if (storage?.state !== 'granted') {
    return (
      <div className="card card--pad stack narrow">
        <h2 className="card__title">
          <Icon name="lock" size={22} /> Recording is locked
        </h2>
        <p>
          {participant.display_name} hasn’t given permission for Roots to keep their recording
          {storage?.state === 'declined' && ' (they chose not to)'}
          {storage?.state === 'withdrawn' && ' (it was withdrawn)'}. Nothing can be recorded or
          uploaded until they do.
        </p>
        <div>
          <ButtonLink to={consentHref} iconRight="arrowRight">
            Go to consent
          </ButtonLink>
        </div>
      </div>
    )
  }

  const selected = mode === 'record' ? recorded : picked
  const durationKnown = mode === 'record' ? true : (picked?.durationKnown ?? false)
  const uploading = uploadState === 'uploading'

  async function upload() {
    if (!selected || !participant || uploading) return
    setUploadState('uploading')
    setUploadError(null)
    setProgress(0)
    try {
      const created = await uploadAudio({
        storyId: story.id,
        participantId: participant.id,
        file: selected.file,
        durationMs: durationKnown ? selected.durationMs : null,
        onProgress: setProgress,
      })
      rememberLocalAudio(created.id, selected.file, selected.file.name)
      updateWorkflow({ storyId: story.id, participantId: participant.id, audioAssetId: created.id })
      setAsset(created)
      setUploadState('uploaded')
      toast.success('Recording saved.')
    } catch (err) {
      setUploadError(describeError(err))
      setUploadState('failed')
    }
  }

  return (
    <div className="stack stack--lg narrow-wide">
      <div className="tabs" role="tablist" aria-label="How to add audio">
        {(['record', 'upload'] as Mode[]).map((m) => (
          <button
            key={m}
            role="tab"
            type="button"
            aria-selected={mode === m}
            className={`tab${mode === m ? ' tab--active' : ''}`}
            disabled={uploading}
            onClick={() => setMode(m)}
          >
            <Icon name={m === 'record' ? 'mic' : 'upload'} size={18} />
            {m === 'record' ? 'Record now' : 'Upload a file'}
          </button>
        ))}
      </div>

      <div className="card card--pad">
        {mode === 'record' ? (
          <AudioRecorder onChange={onRecorded} onSwitchToUpload={() => setMode('upload')} disabled={uploading} />
        ) : (
          <AudioUploader onChange={onPicked} disabled={uploading} />
        )}
      </div>

      {transcription?.state !== 'granted' && (
        <Notice tone="info" title="Transcription permission not granted yet">
          You can save the recording, but a written draft needs “Write down what I say”.{' '}
          <a className="link" href={consentHref} onClick={(e) => { e.preventDefault(); navigate(consentHref) }}>
            Review consent
          </a>
        </Notice>
      )}

      {selected && (
        <section className="card card--pad stack" aria-labelledby="rec-info">
          <h2 id="rec-info" className="card__title">
            Ready to save
          </h2>
          <dl className="facts">
            <div>
              <dt>File</dt>
              <dd>{selected.file.name}</dd>
            </div>
            <div>
              <dt>Length</dt>
              <dd>{durationKnown ? formatDuration(selected.durationMs) : 'Unknown'}</dd>
            </div>
            <div>
              <dt>Size</dt>
              <dd>{formatBytes(selected.file.size)}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                {uploadState === 'idle' && <Badge>Not uploaded</Badge>}
                {uploadState === 'uploading' && <Badge tone="blue">Uploading {Math.round(progress * 100)}%</Badge>}
                {uploadState === 'uploaded' && <Badge tone="green">Saved</Badge>}
                {uploadState === 'failed' && <Badge tone="clay">Failed</Badge>}
              </dd>
            </div>
          </dl>

          {uploading && (
            <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress * 100)} aria-label="Upload progress">
              <div className="progress__bar" style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
          )}

          {uploadError && (
            <Notice tone="error" title="The recording wasn’t saved">
              {uploadError}
            </Notice>
          )}

          {uploadState === 'uploaded' && asset ? (
            <Notice
              tone="success"
              title="Recording saved"
              action={
                <Button iconRight="arrowRight" onClick={() => navigate(`/stories/${story.id}/transcribe?participant=${participant.id}`)}>
                  Continue to transcription
                </Button>
              }
            >
              Stored privately · reference {shortId(asset.id)}
            </Notice>
          ) : (
            <div>
              <Button size="lg" icon="upload" onClick={upload} loading={uploading} disabled={uploading}>
                {uploadState === 'failed' ? 'Try uploading again' : 'Save recording'}
              </Button>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
