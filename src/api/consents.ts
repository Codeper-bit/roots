import { get, post } from './client'
import type { Consent, ConsentCreate, ConsentList, UUID } from '../types'

export const createConsent = (payload: ConsentCreate) => post<Consent>('/consents', payload)

export const listConsents = (participantId: UUID, signal?: AbortSignal) =>
  get<ConsentList>(`/participants/${participantId}/consents`, { signal })

export const withdrawConsent = (consentId: UUID) =>
  post<Consent>(`/consents/${consentId}/withdraw`)
