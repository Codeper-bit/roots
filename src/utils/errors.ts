import { ApiError } from '../api/client'

/** Turns any thrown value into a message a person can act on. */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.kind) {
      case 'network':
        return error.message
      case 'validation':
        return error.message
      case 'consent':
        return `${error.message} The participant needs to grant this permission first.`
      case 'not_found':
        return error.message || 'That item could not be found.'
      case 'too_large':
        return error.message || 'That file is too large.'
      case 'unsupported':
        return error.message || 'That file type is not supported.'
      case 'unavailable':
        return error.message || 'This service is not available right now.'
      case 'server':
        return `The server ran into a problem (${error.status}). ${error.message}`.trim()
      default:
        return error.message
    }
  }
  if (error instanceof Error) return error.message
  return 'Something went wrong.'
}

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404
}
