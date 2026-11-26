import { get } from './client'
import type { HealthResponse } from '../types'

export const checkHealth = (signal?: AbortSignal) => get<HealthResponse>('/health', { signal })
