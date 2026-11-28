import { post } from './client'
import type { ContentVersion, TranslationCreate } from '../types'

// POST /translations is synchronous: it returns the new AI-generated translation
// (an unreviewed content version) once the model has finished, or an error.
export const translateTranscript = (payload: TranslationCreate) =>
  post<ContentVersion>('/translations', payload)
