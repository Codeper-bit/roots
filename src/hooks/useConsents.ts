import { listConsents } from '../api/consents'
import { consentByPurpose } from '../lib/consent'
import type { UUID } from '../types'
import { useAsync } from './useAsync'

export function useConsents(participantId: UUID | null | undefined) {
  const state = useAsync(
    async (signal) => {
      if (!participantId) return null
      const { consents } = await listConsents(participantId, signal)
      return { consents, byPurpose: consentByPurpose(consents) }
    },
    [participantId],
  )
  return state
}
