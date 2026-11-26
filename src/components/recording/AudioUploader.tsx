import { useId, useRef, useState, type DragEvent } from 'react'
import {
  MAX_AUDIO_BYTES,
  MAX_TRANSCRIPTION_BYTES,
  TRANSCRIBABLE_MIME_TYPES,
} from '../../api/audio'
import { formatBytes } from '../../utils/formatDuration'
import { Button } from '../ui/Button'
import { Icon } from '../ui/Icon'
import { Notice } from '../ui/States'
import type { CapturedAudio } from './AudioRecorder'

function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file)
    const audio = new Audio()
    const done = (value: number | null) => {
      URL.revokeObjectURL(url)
      resolve(value)
    }
    audio.preload = 'metadata'
    audio.onloadedmetadata = () =>
      done(Number.isFinite(audio.duration) ? Math.round(audio.duration * 1000) : null)
    audio.onerror = () => done(null)
    audio.src = url
  })
}

export function AudioUploader({
  onChange,
  disabled,
}: {
  onChange: (audio: (CapturedAudio & { durationKnown: boolean }) | null) => void
  disabled?: boolean
}) {
  const inputId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [warning, setWarning] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  async function handleFile(file: File | undefined) {
    setError(null)
    setWarning(null)
    if (!file) return
    if (!file.type.startsWith('audio/')) {
      setError('That doesn’t look like an audio file. Choose an mp3, m4a, wav, ogg, flac or webm recording.')
      onChange(null)
      return
    }
    if (file.size === 0) {
      setError('That file is empty.')
      onChange(null)
      return
    }
    if (file.size > MAX_AUDIO_BYTES) {
      setError(`That file is ${formatBytes(file.size)}. Roots accepts recordings up to ${formatBytes(MAX_AUDIO_BYTES)}.`)
      onChange(null)
      return
    }
    const warnings: string[] = []
    if (file.size > MAX_TRANSCRIPTION_BYTES) {
      warnings.push(
        `Files over ${formatBytes(MAX_TRANSCRIPTION_BYTES)} can be saved but can’t be transcribed by the current speech-to-text service.`,
      )
    }
    if (!TRANSCRIBABLE_MIME_TYPES.includes(file.type)) {
      warnings.push(
        `The format “${file.type}” can be saved, but the current speech-to-text service may not be able to read it.`,
      )
    }
    setWarning(warnings.length ? warnings.join(' ') : null)
    const duration = await readDuration(file)
    onChange({ file, durationMs: duration ?? 0, durationKnown: duration != null })
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragging(false)
    if (!disabled) void handleFile(e.dataTransfer.files[0])
  }

  return (
    <section className="stack" aria-label="Upload a recording">
      <div
        className={`dropzone${dragging ? ' dropzone--drag' : ''}${disabled ? ' dropzone--disabled' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <Icon name="fileAudio" size={32} />
        <p className="dropzone__title">Drop a recording here</p>
        <p className="muted">or choose a file from your device · up to {formatBytes(MAX_AUDIO_BYTES)}</p>
        <label htmlFor={inputId} className="sr-only">
          Choose an audio file
        </label>
        <input
          id={inputId}
          ref={inputRef}
          type="file"
          accept="audio/*"
          className="sr-only"
          disabled={disabled}
          onChange={(e) => {
            void handleFile(e.target.files?.[0])
            e.target.value = ''
          }}
        />
        <Button variant="secondary" icon="upload" onClick={() => inputRef.current?.click()} disabled={disabled}>
          Choose file
        </Button>
      </div>
      {error && (
        <Notice tone="error" title="This file can’t be used">
          {error}
        </Notice>
      )}
      {warning && (
        <Notice tone="warning" title="Heads up">
          {warning}
        </Notice>
      )}
    </section>
  )
}
