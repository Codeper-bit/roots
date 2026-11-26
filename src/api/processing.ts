import { get } from './client'
import type { ProcessingJob, UUID } from '../types'

export const listStoryProcessingJobs = (storyId: UUID, signal?: AbortSignal) =>
  get<ProcessingJob[]>(`/processing-jobs/story/${storyId}`, { signal })
