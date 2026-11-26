import { get, uploadForm } from './client'
import type { AudioAsset, UUID } from '../types'

/** Limits enforced by the backend (routes/audio.py, services/groq_transcription.py). */
export const MAX_AUDIO_BYTES = 50 * 1024 * 1024
export const MAX_TRANSCRIPTION_BYTES = 25 * 1024 * 1024
/** MIME types the transcription engine can read. Uploads accept any audio/*. */
export const TRANSCRIBABLE_MIME_TYPES = [
  'audio/mpeg',
  'audio/mp3',
  'audio/mp4',
  'audio/x-m4a',
  'audio/m4a',
  'audio/wav',
  'audio/x-wav',
  'audio/wave',
  'audio/ogg',
  'audio/flac',
  'audio/webm',
  'video/mp4',
]

export interface UploadAudioInput {
  storyId: UUID
  participantId: UUID
  file: File
  durationMs?: number | null
  onProgress?: (fraction: number) => void
  signal?: AbortSignal
}

// POST /audio-assets/upload — multipart: story_id, participant_id, file, duration_ms?
export function uploadAudio(input: UploadAudioInput): Promise<AudioAsset> {
  const form = new FormData()
  form.append('story_id', input.storyId)
  form.append('participant_id', input.participantId)
  form.append('file', input.file, input.file.name)
  if (input.durationMs != null && Number.isFinite(input.durationMs)) {
    form.append('duration_ms', String(Math.round(input.durationMs)))
  }
  return uploadForm<AudioAsset>('/audio-assets/upload', form, input.onProgress, input.signal)
}

export const getAudioAsset = (audioAssetId: UUID, signal?: AbortSignal) =>
  get<AudioAsset>(`/audio-assets/${audioAssetId}`, { signal })
