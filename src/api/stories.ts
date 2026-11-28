import { get, post } from './client'
import type { Story, StoryCreate, StoryList, UUID } from '../types'

export const createStory = (payload: StoryCreate) => post<Story>('/stories', payload)

// The backend now identifies the owner from the access token; owner_id is still
// sent for compatibility but must match the signed-in user.
export const listStories = (ownerId: UUID, signal?: AbortSignal) =>
  get<StoryList>('/stories', { query: { owner_id: ownerId }, signal })

export const getStory = (storyId: UUID, ownerId: UUID, signal?: AbortSignal) =>
  get<Story>(`/stories/${storyId}`, { query: { owner_id: ownerId }, signal })
