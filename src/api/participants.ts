import { get, post } from './client'
import type { Participant, ParticipantCreate, UUID } from '../types'

export const createParticipant = (payload: ParticipantCreate) =>
  post<Participant>('/participants', payload)

export const listParticipants = (storyId: UUID, signal?: AbortSignal) =>
  get<Participant[]>(`/stories/${storyId}/participants`, { signal })
