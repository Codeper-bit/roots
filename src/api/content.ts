import { ApiError, get, post } from './client'
import type { ContentType, ContentVersion, ContentVersionCreate, UUID } from '../types'

export const createContentVersion = (payload: ContentVersionCreate) =>
  post<ContentVersion>('/content-versions', payload)

export const listContentVersions = (storyId: UUID, signal?: AbortSignal) =>
  get<ContentVersion[]>(`/stories/${storyId}/content-versions`, { signal })

/** Returns null when the backend answers 404 (no such content yet). */
export async function getLatestContent(
  storyId: UUID,
  contentType: ContentType,
  languageCode: string,
  signal?: AbortSignal,
): Promise<ContentVersion | null> {
  try {
    return await get<ContentVersion>(`/stories/${storyId}/content/latest`, {
      query: { content_type: contentType, language_code: languageCode },
      signal,
    })
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null
    throw err
  }
}
