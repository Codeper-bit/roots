// Minimal in-progress workflow context, kept in sessionStorage so a refresh
// mid-workflow does not lose the IDs. Stores ONLY ids returned by the backend:
// never audio, credentials or personal text.
import { useSyncExternalStore } from 'react'
import type { UUID } from '../types'

export interface WorkflowContext {
  storyId?: UUID
  participantId?: UUID
  audioAssetId?: UUID
  transcriptVersionId?: UUID
}

const KEY = 'roots.workflow.v1'
const EVENT = 'roots:workflow'
let cache: WorkflowContext | null = null
let cachedRaw: string | null | undefined

function readRaw(): string | null {
  try {
    return window.sessionStorage.getItem(KEY)
  } catch {
    return null
  }
}

function snapshot(): WorkflowContext {
  const raw = readRaw()
  if (raw === cachedRaw && cache) return cache
  cachedRaw = raw
  try {
    cache = raw ? (JSON.parse(raw) as WorkflowContext) : {}
  } catch {
    cache = {}
  }
  return cache
}

let memory: WorkflowContext = {}

function write(next: WorkflowContext) {
  memory = next
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    /* storage unavailable: memory copy only */
  }
  cache = null
  window.dispatchEvent(new Event(EVENT))
}

export function getWorkflow(): WorkflowContext {
  const stored = snapshot()
  return Object.keys(stored).length > 0 ? stored : memory
}

/** Merge ids into the context. Switching to a different story resets the rest. */
export function updateWorkflow(patch: WorkflowContext) {
  const current = getWorkflow()
  const switching = patch.storyId && current.storyId && patch.storyId !== current.storyId
  write({ ...(switching ? {} : current), ...patch })
}

export function clearWorkflow() {
  write({})
}

function subscribe(cb: () => void) {
  window.addEventListener(EVENT, cb)
  return () => window.removeEventListener(EVENT, cb)
}

export function useWorkflow(): WorkflowContext {
  return useSyncExternalStore(subscribe, getWorkflow)
}

/** Workflow ids, but only if they belong to the story being viewed. */
export function workflowForStory(ctx: WorkflowContext, storyId: UUID): WorkflowContext {
  return ctx.storyId === storyId ? ctx : {}
}
