import { useEffect, useRef } from 'react'
import { useAudioRecorder } from '../../hooks/useAudioRecorder'
import { formatBytes, formatDuration } from '../../utils/formatDuration'
import { Button } from '../ui/Button'
import { Notice } from '../ui/States'
import { AudioPlayer } from './AudioPlayer'
import { Waveform } from './Waveform'

export interface CapturedAudio {
  file: File
  durationMs: number
}

function timestampName(ext: string): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `roots-recording-${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}.${ext}`
}

const STATUS_TEXT: Record<string, string> = {
  idle: 'Ready when you are',
  requesting: 'Waiting for microphone permission…',
  recording: 'Recording',
  paused: 'Paused',
  stopped: 'Recording finished',
  denied: 'Microphone blocked',
  unsupported: 'Recording not supported here',
  error: 'Recording problem',
}

export function AudioRecorder({
  onChange,
  onSwitchToUpload,
  disabled,
}: {
  onChange: (audio: CapturedAudio | null) => void
  onSwitchToUpload: () => void
  disabled?: boolean
}) {
  const rec = useAudioRecorder()
  const notified = useRef<unknown>(null)

  useEffect(() => {
    if (rec.result && notified.current !== rec.result) {
      notified.current = rec.result
      const file = new File([rec.result.blob], timestampName(rec.result.extension), {
        type: rec.result.mimeType,
      })
      onChange({ file, durationMs: rec.result.durationMs })
    }
  }, [rec.result, onChange])

  const live = rec.state === 'recording' || rec.state === 'paused'
  const resultUrlRef = useRef<{ blob: Blob; url: string } | null>(null)
  let previewUrl: string | null = null
  if (rec.result) {
    if (resultUrlRef.current?.blob !== rec.result.blob) {
      if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current.url)
      resultUrlRef.current = { blob: rec.result.blob, url: URL.createObjectURL(rec.result.blob) }
    }
    previewUrl = resultUrlRef.current.url
  }
  useEffect(
    () => () => {
      if (resultUrlRef.current) URL.revokeObjectURL(resultUrlRef.current.url)
    },
    [],
  )

  return (
    <section className="studio" aria-label="Recorder">
      <div className="studio__status" aria-live="polite">
        <span className={`rec-dot rec-dot--${rec.state}`} aria-hidden="true" />
        <span className="studio__status-text">{STATUS_TEXT[rec.state]}</span>
      </div>

      <Waveform
        analyser={rec.analyser}
        active={rec.state === 'recording'}
        clear={rec.state === 'idle' || rec.state === 'requesting'}
      />

      <div className="studio__timer" role="timer" aria-label="Recording time">
        {formatDuration(rec.elapsedMs)}
      </div>

      {rec.state === 'denied' && (
        <Notice tone="warning" title="Roots can’t hear the microphone">
          Your browser blocked microphone access. Allow it from the site settings next to the address
          bar and try again, or upload a recording you already have.
          <div className="notice__action row">
            <Button size="sm" onClick={rec.start}>
              Try again
            </Button>
            <Button size="sm" variant="secondary" onClick={onSwitchToUpload}>
              Upload a file instead
            </Button>
          </div>
        </Notice>
      )}
      {rec.state === 'unsupported' && (
        <Notice tone="warning" title="This browser can’t record audio">
          Recording needs a browser with microphone support and a secure (https or localhost)
          connection. You can still upload a recording.
          <div className="notice__action">
            <Button size="sm" variant="secondary" onClick={onSwitchToUpload}>
              Upload a file instead
            </Button>
          </div>
        </Notice>
      )}
      {rec.state === 'error' && rec.error && (
        <Notice tone="error" title="Something went wrong">
          {rec.error}
        </Notice>
      )}

      <div className="studio__controls">
        {(rec.state === 'idle' || rec.state === 'requesting' || rec.state === 'error' || rec.state === 'denied') && (
          <Button
            size="lg"
            icon="mic"
            onClick={rec.start}
            loading={rec.state === 'requesting'}
            disabled={disabled}
          >
            Start recording
          </Button>
        )}
        {live && (
          <>
            {rec.canPause &&
              (rec.state === 'recording' ? (
                <Button variant="secondary" size="lg" icon="pause" onClick={rec.pause}>
                  Pause
                </Button>
              ) : (
                <Button variant="secondary" size="lg" icon="play" onClick={rec.resume}>
                  Resume
                </Button>
              ))}
            <Button variant="danger" size="lg" icon="stop" onClick={rec.stop}>
              Stop
            </Button>
          </>
        )}
        {rec.state === 'stopped' && (
          <Button
            variant="secondary"
            icon="rotate"
            onClick={() => {
              notified.current = null
              rec.reset()
              onChange(null)
            }}
            disabled={disabled}
          >
            Re-record
          </Button>
        )}
      </div>

      {rec.state === 'stopped' && rec.result && previewUrl && (
        <div className="studio__preview">
          <p className="muted">
            Listen back before you save it · {formatBytes(rec.result.blob.size)}
          </p>
          <AudioPlayer src={previewUrl} durationHintMs={rec.result.durationMs} label="Preview of your recording" />
        </div>
      )}
    </section>
  )
}
