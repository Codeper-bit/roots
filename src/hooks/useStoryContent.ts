import { listContentVersions } from '../api/content'
import type { ContentVersion, Story } from '../types'
import { useAsync } from './useAsync'

export interface StoryContent {
  story: Story
  versions: ContentVersion[]
}

/** Latest version per (type, language) for each story: the unit review works on. */
export function latestVersions(versions: ContentVersion[]): ContentVersion[] {
  const latest = new Map<string, ContentVersion>()
  for (const v of versions) {
    const key = `${v.content_type}:${v.language_code}`
    const current = latest.get(key)
    if (!current || v.version_number > current.version_number) latest.set(key, v)
  }
  return [...latest.values()]
}

const MAX_STORIES = 40

/**
 * The backend has no endpoint that lists content across stories, so this
 * fetches each story's versions (one request per story, in parallel).
 * Stories beyond MAX_STORIES are not included; `truncated` reports that.
 */
export function useStoriesContent(stories: Story[] | null) {
  const ids = stories ? stories.map((s) => s.id).join(',') : ''
  const state = useAsync<{ items: StoryContent[]; truncated: boolean }>(
    async (signal) => {
      if (!stories) return { items: [], truncated: false }
      const slice = stories.slice(0, MAX_STORIES)
      const items = await Promise.all(
        slice.map(async (story) => ({
          story,
          versions: await listContentVersions(story.id, signal),
        })),
      )
      return { items, truncated: stories.length > MAX_STORIES }
    },
    [ids],
  )
  return state
}
