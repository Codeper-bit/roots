import { post } from './client'
import type { ContentVersion, TranscriptionCreate } from '../types'

// POST /transcriptions is synchronous: it returns the new transcript content
// version once the engine has finished (or an error if it failed).
export const transcribe = (payload: TranscriptionCreate) =>
  post<ContentVersion>('/transcriptions', payload)
