// Audio recorded or chosen in THIS tab, kept in memory only (never persisted).
// The backend currently has no download or signed-URL endpoint, so this is the
// only way to play a recording back, and only until the page is refreshed.
import type { UUID } from '../types'

interface LocalAudio {
  url: string
  fileName: string
}

const byAsset = new Map<UUID, LocalAudio>()

export function rememberLocalAudio(audioAssetId: UUID, file: Blob, fileName: string) {
  const previous = byAsset.get(audioAssetId)
  if (previous) URL.revokeObjectURL(previous.url)
  byAsset.set(audioAssetId, { url: URL.createObjectURL(file), fileName })
}

export function getLocalAudio(audioAssetId: UUID | undefined | null): LocalAudio | null {
  return audioAssetId ? (byAsset.get(audioAssetId) ?? null) : null
}
