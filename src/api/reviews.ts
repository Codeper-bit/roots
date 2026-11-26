import { get, post } from './client'
import type { ContentReview, ContentReviewCreate, UUID } from '../types'

export const createReview = (payload: ContentReviewCreate) =>
  post<ContentReview>('/content-reviews', payload)

export const listReviewsForVersion = (contentVersionId: UUID, signal?: AbortSignal) =>
  get<ContentReview[]>(`/content-reviews/version/${contentVersionId}`, { signal })
