import { listStories } from '../api/stories'
import type { UUID } from '../types'
import { useAsync } from './useAsync'

export function useStories(ownerId: UUID) {
  return useAsync((signal) => listStories(ownerId, signal), [ownerId])
}
