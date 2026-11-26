import { get, patch, post } from './client'
import type { StoryQuestion, StoryQuestionList, StoryQuestionStatus, UUID } from '../types'

export const createStoryQuestion = (storyId: UUID, question: string) =>
  post<StoryQuestion>('/story-questions', { story_id: storyId, question })

export const listStoryQuestions = (storyId: UUID, signal?: AbortSignal) =>
  get<StoryQuestionList>(`/stories/${storyId}/questions`, { signal })

export const updateStoryQuestionStatus = (questionId: UUID, status: StoryQuestionStatus) =>
  patch<StoryQuestion>(`/story-questions/${questionId}/status`, { status })
